from __future__ import annotations

import configparser
from collections import defaultdict
import itertools
import logging
from pathlib import Path
import re

from charm.lib.errors import MetadataParseError, NoChartsError, NoMetadataError, ChartParseError, ChartPostReadParseError
from charm.lib.types import Seconds
from charm.refactor.charts.hero import HeroChart, HeroNote, HeroChord, Ticks, BPMChangeTickEvent, TextEvent, SoloEvent
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


def create_chart_chords(chart: HeroChart) -> None:
    """
    Turn lists of notes (in `self.notes`) into `HeroChord`s (in `self.chords`)
    A chord is defined as all notes occuring at the same tick.
    While this could be a method on HeroChart I am keeping it
    seperate to keep parsing of hero charts all in one file ~Dragon
    """
    c = defaultdict(list)
    for note in chart.notes:
        c[note.tick].append(note)
    chord_lists = list(c.values())
    chords = []
    for cl in chord_lists:
        chords.append(HeroChord(cl))
    chart.chords = chords

def calculate_chart_note_flags(chart: HeroChart) -> None:
    """Turn notes that aren't really notes but flags into properties on the notes."""
    for c in chart.chords:
        forced = False
        tap = False
        for n in c.notes:
            if n.lane == 5:  # HOPO force
                forced = True
            elif n.lane == 6:  # Tap
                tap = True
        for n in c.notes:
            # Tap overrides HOPO, intentionally.
            if tap:
                n.type = "tap"
            elif forced:
                n.type = "forced"
        c = HeroChord([n for n in c.notes if n.lane not in [5, 6]])

def calculate_chart_hopos(chart: HeroChart) -> None:
    # TODO: requires the chart's NIndex
    pass

def parse_chart_text_events(chart: HeroChart) -> None:
    current_solo = None
    for e in chart.events_by_type(TextEvent):
        if e.text == "solo":
            current_solo = e
        elif e.text == "soloend":
            if current_solo is None:
                raise ChartPostReadParseError("`solo_end` without `solo` event!")
            tick_length = e.tick - current_solo.tick
            length = e.time - current_solo.time
            chart.events.append(SoloEvent(current_solo.time, current_solo.tick, tick_length, length))
            current_solo = None
        chart.events.remove(e)

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
        if not (chart_data.path).exists():
            raise NoChartsError(chart_data.path.stem)
        with open(chart_data.path, encoding = "utf-8") as f:
            chartfile = f.readlines()

        target_header = f"{chart_data.difficulty}{chart_data.instrument}"
        reached_target_chart = False

        resolution: Ticks = 192
        offset: Seconds = 0

        chart = HeroChart(chart_data, [], [], 0)

        current_header = None
        sync_track: list[BPMChangeTickEvent] = []

        for line_num, line in enumerate(chartfile):
            line = line.strip().strip("\uffef").strip("\ufeff")  # god dang ffef

            # Screw curly braces
            if line == "{" or line == "}":
                continue

            # Parse headers
            if m := re.match(RE_HEADER, line):
                header = m.group(1)
                if header not in VALID_HEADERS:
                    raise ChartParseError(line_num, f"{header} is not a valid header.")
                if current_header is None and header != "Song":
                    raise ChartParseError(line_num, "First header must be Song.")
                current_header = header
                continue

            match current_header:
                case "song":
                    continue
                case "SyncTrack":
                    if m := re.match(RE_A, line):
                        # ignore anchor events [only used for charting]
                        continue
                    # BPM Events
                    elif m := re.match(RE_B, line):
                        tick, mbpm = (int(i) for i in m.groups())
                        if not sync_track and tick != 0:
                            raise ChartParseError(line_num, "Chart has no BPM event at tick 0.")
                        if not sync_track:
                            sync_event = BPMChangeTickEvent(0, tick, mbpm / 1000)
                        else:
                            seconds = tick_to_seconds(tick, sync_track, resolution, offset)
                            sync_event = BPMChangeTickEvent(seconds, tick, mbpm / 1000)
                        chart.events.append(sync_event)
                        sync_track.append(sync_event)
                    # Time Sig events
                    elif m := re.match(RE_TS, line):
                        tick, num, denom = m.groups()
                        tick = int(tick)
                        denom = 4 if denom is None else int(denom) ** 2
                        seconds = tick_to_seconds(tick, sync_track, resolution, offset)
                        chart.events.append(TSEvent(seconds, tick, int(num), int(denom)))
                    else:
                        raise ChartParseError(line_num, f"Non-sync event in SyncTrack: {line!r}")
                case "Events":
                    # Section events
                    if m := re.match(RE_SECTION, line):
                        tick, name = m.groups()
                        tick = int(tick)
                        seconds = tick_to_seconds(tick, sync_track, resolution, offset)
                        chart.events.append(SectionEvent(seconds, tick, name))
                    # Lyric events
                    elif m := re.match(RE_LYRIC, line):
                        tick, text = m.groups()
                        tick = int(tick)
                        seconds = tick_to_seconds(tick, sync_track, resolution, offset)
                        chart.events.append(RawLyricEvent(seconds, tick, text))
                    # Misc. events
                    elif m := re.match(RE_E, line):
                        tick, text = m.groups()
                        tick = int(tick)
                        seconds = tick_to_seconds(tick, sync_track, resolution, offset)
                        chart.events.append(TextEvent(seconds, tick, text))
                    else:
                        raise ChartParseError(line_num, f"Non-event in Events: {line!r}")
                case _:
                    if current_header != target_header:
                        if reached_target_chart:
                            break
                        continue
                    reached_target_chart = True
                    # Track events
                    if m := re.match(RE_TRACK_E, line):
                        tick, text = m.groups()
                        tick = int(tick)
                        seconds = tick_to_seconds(tick, sync_track, resolution, offset)
                        chart.events.append(TextEvent(seconds, tick, text))
                    # Note events
                    elif m := re.match(RE_N, line):
                        tick, lane, length = m.groups()
                        tick = int(tick)
                        length = int(length)
                        seconds = tick_to_seconds(tick, sync_track, resolution, offset)
                        end = tick_to_seconds(tick + length, sync_track, resolution, offset)
                        sec_length = round(end - seconds, 5)  # accurate to 1/100ms
                        chart.notes.append(HeroNote(chart, seconds, int(lane), sec_length, tick = tick, tick_length = length))  # TODO: Note flags.
                    # Special events
                    elif m := re.match(RE_S, line):
                        tick, s_type, length = m.groups()
                        tick = int(tick)
                        length = int(length)
                        seconds = tick_to_seconds(tick, sync_track, resolution, offset)
                        end = tick_to_seconds(tick + length, sync_track, resolution, offset)
                        sec_length = round(end - seconds, 5)  # accurate to 1/100ms
                        if s_type == "2":
                            chart.events.append(StarpowerEvent(seconds, tick, length, sec_length))
                    # Ignoring non-SP events for now...
                    else:
                        raise ChartParseError(line_num, f"Non-chart event in {current_header}: {line!r}")

        create_chart_chords(chart)
        calculate_chart_note_flags(chart)
        parse_chart_text_events(chart)
        chart.events.sort()
        #TODO: NIndex time signature
        calculate_chart_hopos(chart)
        # TODO: calculate chart beats
        # TODO: process chart lyrics

        #TODO: NIndex rest of the chart properties

        return [chart]
