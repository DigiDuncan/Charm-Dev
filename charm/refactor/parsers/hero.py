from __future__ import annotations

import configparser
from dataclasses import dataclass
import itertools
import logging
from pathlib import Path
import re
from typing import NotRequired, TypedDict

from nindex.index import Index
from charm.lib.errors import MetadataParseError, NoChartsError, NoMetadataError
from charm.lib.types import Seconds
from charm.refactor.charts.hero import HeroChart, HeroNote, Ticks
from charm.refactor.generic.chart import ChartMetadata, Event, Note
from charm.refactor.generic.metadata import ChartSetMetadata
from charm.refactor.generic.parser import Parser

logger = logging.getLogger("charm")

RE_HEADER = r"\[(.+)\]"
RE_DATA = r"([^\s]+)\s*=\s*\"?([^\"]+)\"?"

RE_B = r"(\d+)\s*=\s*B\s(\d+)"  # BPM Event
RE_TS = r"(\d+)\s*=\s*TS\s(\d+)\s?(\d+)?"  # Time Sig Event
RE_A = r"(\d+)\s*=\s*A\s(\d+)"  # Anchor Event (unused by games, editor only)
RE_E = r"(\d+)\s*=\s*E\s\"(.*)\""  # Text Event (basically anything, fun)
RE_SECTION = r"(\d+)\s*=\s*E\s\"section (.*)\""  # Section Event (subtype of E)
RE_LYRIC = r"(\d+)\s*=\s*E\s\"lyric (.*)\""  # Lyric Event (subtype of E)
RE_N = r"(\d+)\s*=\s*N\s(\d+)\s?(\d+)?"  # Note Event (or note flag event...)
RE_S = r"(\d+)\s*=\s*S\s(\d+)\s?(\d+)?"  # "Special Event" (really guys?)
RE_STARPOWER = r"(\d+)\s*=\s*S\s2\s?(\d+)?"  # Starpower Event (subtype of S)
RE_TRACK_E = r"(\d+)\s*=\s*E\s([^\s]+)"  # Track Event (text event but with no quotes)

DIFFICULTIES = ["Easy", "Medium", "Hard", "Expert"]
INSTRUMENTS = ["Single", "DoubleGuitar", "DoubleBass", "DoubleRhythm", "Drums", "Keyboard", "GHLGuitar", "GHLBass"]
SPECIAL_HEADERS = ["Song", "SyncTrack", "Events"]
# Produce every unique pair of difficulties and instruments (e.g.: EasySingle) and map them to tuples (e.g.: (Easy, Single))
DIFF_INST_MAP: dict[str, tuple[str, str]] = {(a + b): (a, b) for a, b in itertools.product(DIFFICULTIES, INSTRUMENTS)}
VALID_HEADERS = list(DIFF_INST_MAP.keys()) + SPECIAL_HEADERS

@dataclass
class TickEvent(Event):
    tick: int

    def __lt__(self, other: TickEvent) -> bool:
        return self.tick < other.tick

@dataclass
class TSEvent(TickEvent):
    numerator: int
    denominator: int = 4

    @property
    def time_sig(self) -> tuple[int, int]:
        return (self.numerator, self.denominator)

@dataclass
class TextEvent(TickEvent):
    text: str

@dataclass
class SectionEvent(TickEvent):
    name: str

@dataclass
class RawLyricEvent(TickEvent):
    text: str

@dataclass
class StarpowerEvent(TickEvent):
    tick_length: Ticks
    length: Seconds

@dataclass
class SoloEvent(TickEvent):
    tick_length: Ticks
    length: Seconds

@dataclass
class BPMChangeTickEvent(TickEvent):
    new_bpm: float

@dataclass
class BeatEvent(TickEvent):
    id: int
    major: bool = True

@dataclass
class RawBPMEvent:
    """Only used for parsing, and shouldn't be in a Song post-parse."""
    ticks: Ticks
    mbpm: int

class IndexDict[T](TypedDict):
    bpm: NotRequired[Index[T, BPMChangeTickEvent]]
    time_sig: NotRequired[Index[T, TSEvent]]
    section: NotRequired[Index[T, SectionEvent]]
    beat: NotRequired[Index[T, BeatEvent]]
    note: NotRequired[Index[T, Note]]
    chord: NotRequired[Index[T, HeroChord]]

class HeroChord:
    """A data object to hold notes and have useful functions for manipulating and reading them."""
    def __init__(self, notes: list[HeroNote] | None = None) -> None:
        self.notes = notes if notes else []

    @property
    def frets(self) -> tuple[int, ...]:
        return tuple(set(n.lane for n in self.notes))

    @property
    def tick(self) -> Ticks | None:
        return self.notes[0].tick

    @property
    def tick_length(self) -> Ticks:
        return max([n.tick_length for n in self.notes if n.tick_length is not None])

    @property
    def tick_end(self) -> Ticks | None:
        return self.tick + self.tick_length if self.tick is not None else None

    @property
    def time(self) -> Seconds:
        return self.notes[0].time

    @property
    def length(self) -> Seconds:
        return max([n.length for n in self.notes])

    @property
    def end(self) -> Seconds:
        return self.time + self.length

    @property
    def type(self) -> str:
        return self.notes[0].type

    @type.setter
    def type(self, v: str) -> None:
        for n in self.notes:
            n.type = v

    @property
    def hit(self) -> bool:
        return self.notes[0].hit

    @hit.setter
    def hit(self, v: bool) -> None:
        for n in self.notes:
            n.hit = v

    @property
    def hit_time(self) -> Seconds | None:
        return self.notes[0].hit_time

    @hit_time.setter
    def hit_time(self, v: Seconds) -> None:
        for n in self.notes:
            n.hit_time = v

    @property
    def missed(self) -> bool:
        return self.notes[0].missed

    @missed.setter
    def missed(self, v: bool) -> None:
        for n in self.notes:
            n.missed = v

    @property
    def valid_shapes(self) -> list[list[bool]]:
        if 7 in self.frets:
            return [[False] * 5]
        if len(self.frets) > 1:
            return [[n in self.frets for n in range(5)]]
        b = [False, True]
        max_fret = max(self.frets)
        valid_shape_list = [list(v) for v in itertools.product(b, repeat = max_fret)]
        append_part = [True] + ([False] * (4 - max_fret))
        final_list = [v + append_part for v in valid_shape_list]
        return final_list

def tick_to_seconds(current_tick: Ticks, sync_track: list[BPMChangeTickEvent], resolution: int = 192, offset: float = 0) -> Seconds:
    """Takes a tick (and an associated sync_track,) and returns its position in seconds as a float."""
    if current_tick == 0:
        return 0
    bpm_events = [b for b in sync_track if b.tick <= current_tick]
    bpm_events.sort(key=lambda x: x.tick)
    last_bpm_event = bpm_events[-1]
    tick_delta = current_tick - last_bpm_event.tick
    bps = last_bpm_event.new_bpm / 60
    seconds = tick_delta / (resolution * bps)
    return seconds + offset + last_bpm_event.time

class HeroParser(Parser[HeroChart]):
    @staticmethod
    def is_parseable(path: Path) -> bool:
        return path.suffix == ".chart"

    @staticmethod
    def parse_chartset_metadata(path: Path) -> ChartSetMetadata:
        if not (path / "song.ini").exists():
            raise NoMetadataError(path.stem)
        parser = configparser.ConfigParser()
        parser.read((path / "song.ini").absolute())
        if "song" not in parser:
            raise MetadataParseError("Song header not found in metadata!")
        song = parser["song"]
        return ChartSetMetadata(
            path=path,
            title=song["name"],
            artist=song["artist"],
            album=song["album"],
            length=song.getfloat("song_length") / 1000,
            genre=song["genre"],
            year=song.getint("year"),
            charter=song["charter"],
            gamemode="hero"
        )

    @staticmethod
    def parse_metadata(path: Path) -> list[ChartMetadata]:
        metadatas = []
        if not (path / "notes.chart").exists():
            raise NoChartsError(path.stem)
        with open(path / "notes.chart", encoding = "utf-8") as f:
            chartfile = f.readlines()

        for line in chartfile:
            line = line.strip().strip("\uffef").strip("\ufeff")  # god dang ffef
            if m := re.match(RE_HEADER, line):
                header = m.group(1)
                if header in DIFF_INST_MAP:
                    diff, inst = DIFF_INST_MAP[header]
                    metadatas.append(ChartMetadata("hero", diff, path, inst))

        return metadatas

    @staticmethod
    def parse_chart(chart_data: ChartMetadata) -> list[HeroChart]:
        raise NotImplementedError
