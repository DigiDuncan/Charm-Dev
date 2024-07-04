from __future__ import annotations

from importlib.resources import files
from collections import defaultdict
from functools import cache
from typing import Literal, cast, TypedDict, Generator, Any, NamedTuple
from dataclasses import dataclass
from pathlib import Path
import configparser
import itertools
import logging
import math
import re

from nindex import Index
import PIL.Image
import arcade
from arcade import Sprite, Texture, SpriteList, color as colors
from arcade.types import Color
from arcade.camera import PerspectiveProjector
from arcade.camera.data_types import duplicate_camera_data

from charm.lib.charm import load_missing_texture
from charm.lib.errors import ChartParseError, ChartPostReadParseError, NoChartsError, NoMetadataError, MetadataParseError
from charm.lib.generic.engine import DigitalKeyEvent, Engine, Judgement
from charm.lib.generic.highway import Highway
from charm.lib.generic.song import Chart, Event, Metadata, Note, Seconds, Song
from charm.lib.keymap import Action, keymap
from charm.lib.utils import img_from_path, nuke_smart_quotes
from charm.objects.lyric_animator import LyricEvent
from charm.lib.pool import Pool

from charm.objects.line_renderer import LongNoteRenderer
import charm.data.images.skins as skins

logger = logging.getLogger("charm")

note_id = -1

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

Ticks = int


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

# ---


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


class NoteColor:
    GREEN = colors.LIME_GREEN
    RED = colors.RED
    YELLOW = colors.YELLOW
    BLUE = colors.BLUE
    ORANGE = colors.ORANGE
    PURPLE = colors.PURPLE

    @classmethod
    def from_note(cls, note: HeroNote) -> Color:
        match note.lane:
            case 0:
                return cls.GREEN
            case 1:
                return cls.RED
            case 2:
                return cls.YELLOW
            case 3:
                return cls.BLUE
            case 4:
                return cls.ORANGE
            case 7:
                return cls.PURPLE
            case _:
                return colors.BLACK


@dataclass
class HeroNote(Note):
    tick: int = None
    tick_length: Ticks = None

    @property
    def icon(self) -> str:
        return super().icon

    def __str__(self) -> str:
        return f"<HeroNote T:{self.tick}{'+' + str(self.tick_length) if self.tick_length else ''} ({round(self.time, 3)}) lane={self.lane} type={self.type} length={round(self.length)}>"

    def __repr__(self) -> str:
        return self.__str__()


class HeroChord:
    """A data object to hold notes and have useful functions for manipulating and reading them."""
    def __init__(self, notes: list[HeroNote] = None) -> None:
        self.notes = notes if notes else []

    @property
    def frets(self) -> tuple[int]:
        return tuple(set(n.lane for n in self.notes))

    @property
    def tick(self) -> Ticks:
        return self.notes[0].tick

    @property
    def tick_length(self) -> Ticks:
        return max([n.tick_length for n in self.notes])

    @property
    def tick_end(self) -> Ticks:
        return self.tick + self.tick_length

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
    def hit_time(self) -> Seconds:
        return self.notes[0].hit_time

    @hit_time.setter
    def hit_time(self, v: Seconds) -> None:
        for n in self.notes:
            n.hit_time = v

    @property
    def missed(self) -> bool:
        return self.notes[0].missed

    @missed.setter
    def missed(self, v) -> None:
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


class IndexDict[T](TypedDict):
    bpm: Index[T, BPMChangeTickEvent]
    time_sig: Index[T, TSEvent]
    section: Index[T, SectionEvent]
    beat: Index[T, BeatEvent]
    note: Index[T, Note]
    chord: Index[T, HeroChord]


class HeroChart(Chart):
    def __init__(self, song: Song[HeroChart], difficulty: str, instrument: str, lanes: int, hash: str | None) -> None:
        super().__init__(song, "hero", difficulty, instrument, lanes, hash)
        self.song: HeroSong = self.song
        self.chords: list[HeroChord] = None

        self.indexes_by_tick: IndexDict[Ticks] = {}
        self.indexes_by_time: IndexDict[Seconds] = {}

    def finalize(self) -> None:
        """Do some last-pass parsing steps."""
        self.create_chords()
        self.calculate_note_flags()
        self.calculate_hopos()
        self.parse_text_events()
        self.index()

    def create_chords(self) -> None:
        """Turn lists of notes (in `self.notes`) into `HeroChord`s (in `self.chords`)
        A chord is defined as all notes occuring at the same tick."""
        c = defaultdict(list)
        for note in self.notes:
            c[note.tick].append(note)
        chord_lists = list(c.values())
        chords = []
        for cl in chord_lists:
            chords.append(HeroChord(cl))
        self.chords = chords

    def calculate_note_flags(self) -> None:
        """Turn notes that aren't really notes but flags into properties on the notes."""
        for c in self.chords:
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

    def calculate_hopos(self) -> None:
        # This is basically ripped from Charm-Legacy.
        # https://github.com/DigiDuncan/Charm-Legacy/blob/3187a8f2fa8c8876c2706b731bff6913dc0bad60/charm/song.py#L179
        for last_chord, current_chord in zip(self.chords[:-1], self.chords[1:]):  # python zip pattern, wee
            timesig = self.song.indexes_by_tick["time_sig"].lteq(last_chord.tick)
            if timesig is None:
                timesig = TSEvent(0, 0, 4, 4)

            ticks_per_quarternote = self.song.resolution
            ticks_per_wholenote = ticks_per_quarternote * 4
            # Why can the time signature be X/0? What? What is that supposed to parse as? :amtired:
            beats_per_wholenote = timesig.denominator if timesig.denominator != 0 else 0.5
            ticks_per_beat = ticks_per_wholenote / beats_per_wholenote

            chord_distance = current_chord.tick - last_chord.tick

            hopo_cutoff = ticks_per_beat / (192 / 66)  # Why? Where does this number come from?
                                                       # It's like 1/81th more than 1/3? Why?
                                                       # This value was scraped from Moonscraper so I trust it.

            if current_chord.frets == last_chord.frets:
                # You can't have two HOPO chords of the same fretting.
                if current_chord.type == "forced":
                    current_chord.type = "normal"
            elif chord_distance <= hopo_cutoff:
                if current_chord.type == "forced":
                    current_chord.type = "normal"
                elif current_chord.type == "normal":
                    current_chord.type = "hopo"
            else:
                if current_chord.type == "forced":
                    current_chord.type = "hopo"

    def parse_text_events(self) -> None:
        self.events = cast("list[TickEvent]", self.events)
        parsed: list[TextEvent] = []
        new_events: list[SoloEvent] = []
        current_solo = None
        for e in [e for e in self.events if isinstance(e, TextEvent)]:
            if e.text == "solo":
                current_solo = e
                parsed.append(e)
            elif e.text == "soloend":
                if current_solo is None:
                    raise ChartPostReadParseError("`solo_end` without `solo` event!")
                tick_length = e.tick - current_solo.tick
                length = e.time - current_solo.time
                new_events.append(SoloEvent(current_solo.time, current_solo.tick, tick_length, length))
                current_solo = None
                parsed.append(e)
        for e in parsed:
            self.events.remove(e)
        for e in new_events:
            self.events.append(e)
        self.events.sort()

    def index(self) -> None:
        self.indexes_by_tick["note"] = Index[Ticks, Note](self.notes, "tick")
        self.indexes_by_tick["chord"] = Index[Ticks, HeroChord](self.chords, "tick")

        self.indexes_by_time["note"] = Index[Seconds, Note](self.notes, "time")
        self.indexes_by_time["chord"] = Index[Seconds, HeroChord](self.chords, "time")


class HeroSong(Song[HeroChart]):
    def __init__(self, path: Path):
        super().__init__(path)
        self.indexes_by_tick: IndexDict = {}
        self.indexes_by_time: IndexDict = {}
        self.resolution: int = 192  # ticks/beat
        self.metadata = Metadata(path=path, title="Unknown Title")

    def get_metadata(self, folder: Path) -> Metadata:
        if not (folder / "song.ini").exists():
            raise NoMetadataError(folder.stem)
        parser = configparser.ConfigParser()
        parser.read((folder / "song.ini").absolute())
        if "song" not in parser:
            raise MetadataParseError("Song header not found in metadata!")
        song = parser["song"]
        return Metadata(
            path=folder,
            title=song["name"],
            artist=song["artist"],
            album=song["album"],
            length=song.getfloat("song_length") / 1000,
            genre=song["genre"],
            year=song.getint("year"),
            charter=song["charter"],
            gamemode="hero"
        )

    @classmethod
    def parse(cls, path: Path) -> HeroSong:
        if not (path / "notes.chart").exists():
            raise NoChartsError(path.stem)
        with open(path / "notes.chart", encoding = "utf-8") as f:
            chartfile = f.readlines()

        resolution: Ticks = 192
        offset: Seconds = 0
        metadata = Metadata(path=path, title="Unknown Title")
        charts: dict[str, HeroChart] = {}
        events: list[Event] = []

        current_header = None
        line_num = 0
        sync_track: list[BPMChangeTickEvent] = []

        for line in chartfile:
            line = line.strip().strip("\uffef").strip("\ufeff")  # god dang ffef
            line_num += 1

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
            # Parse metadata
            elif current_header == "Song":
                if m := re.match(RE_DATA, line):
                    match m.group(1):
                        case "Resolution":
                            resolution = Ticks(m.group(2))
                        case "Name":
                            metadata.title = m.group(2)
                        case "Artist":
                            metadata.artist = m.group(2)
                        case "Album":
                            metadata.album = m.group(2)
                        case "Year":
                            metadata.year = int(m.group(2).removeprefix(",").strip())
                        case "Charter":
                            metadata.charter = m.group(2)
                        case "Offset":
                            offset = Seconds(m.group(2))
                        # Skipping "Player2"
                        case "Difficulty":
                            metadata.difficulty = int(m.group(2))
                        case "PreviewStart":
                            metadata.preview_start = Seconds(m.group(2))
                        case "PreviewEnd":
                            metadata.preview_end = Seconds(m.group(2))
                        case "Genre":
                            metadata.genre = m.group(2)
                        # Skipping "MediaType"
                        # Skipping "Audio streams"
                        case "Player2" | "MediaType":
                            pass
                        case _:
                            logger.debug(f"Unrecognized .chart metadata {line!r}")
                else:
                    raise ChartParseError(line_num, f"Non-metadata found in metadata section: {line!r}")
            elif current_header == "SyncTrack":
                if m := re.match(RE_A, line):
                    # ignore anchor events [only used for charting]
                    continue
                # BPM Events
                elif m := re.match(RE_B, line):
                    tick, mbpm = [int(i) for i in m.groups()]
                    tick = int(tick)
                    if not sync_track and tick != 0:
                        raise ChartParseError(line_num, "Chart has no BPM event at tick 0.")
                    if not sync_track:
                        events.append(BPMChangeTickEvent(0, tick, mbpm / 1000))
                        sync_track.append(BPMChangeTickEvent(0, tick, mbpm / 1000))
                    else:
                        seconds = tick_to_seconds(tick, sync_track, resolution, offset)
                        events.append(BPMChangeTickEvent(seconds, tick, mbpm / 1000))
                        sync_track.append(BPMChangeTickEvent(seconds, tick, mbpm / 1000))
                # Time Sig events
                elif m := re.match(RE_TS, line):
                    tick, num, denom = m.groups()
                    tick = int(tick)
                    denom = 4 if denom is None else int(denom) ** 2
                    seconds = tick_to_seconds(tick, sync_track, resolution, offset)
                    events.append(TSEvent(seconds, tick, int(num), int(denom)))
                else:
                    raise ChartParseError(line_num, f"Non-sync event in SyncTrack: {line!r}")
            # Events sections
            elif current_header == "Events":
                # Section events
                if m := re.match(RE_SECTION, line):
                    tick, name = m.groups()
                    tick = int(tick)
                    seconds = tick_to_seconds(tick, sync_track, resolution, offset)
                    events.append(SectionEvent(seconds, tick, name))
                # Lyric events
                elif m := re.match(RE_LYRIC, line):
                    tick, text = m.groups()
                    tick = int(tick)
                    seconds = tick_to_seconds(tick, sync_track, resolution, offset)
                    events.append(RawLyricEvent(seconds, tick, text))
                # Misc. events
                elif m := re.match(RE_E, line):
                    tick, text = m.groups()
                    tick = int(tick)
                    seconds = tick_to_seconds(tick, sync_track, resolution, offset)
                    events.append(TextEvent(seconds, tick, text))
                else:
                    raise ChartParseError(line_num, f"Non-event in Events: {line!r}")
            else:
                # We are in a chart section
                diff, inst = DIFF_INST_MAP[current_header]
                if current_header not in charts:
                    charts[current_header] = HeroChart(None, diff, inst, 5, None)
                chart = charts[current_header]
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

        # Finalize
        song = HeroSong(metadata.path)
        song.events.extend(events)
        song.events.sort()
        song.index()
        for chart in charts.values():
            chart.song = song
            chart.finalize()
            song.charts.append(chart)
        song.calculate_beats()
        song.events.sort()  # why is it like this
        song.process_lyrics()
        song.index()  # oh god help
        song.resolution = resolution
        song.metadata = metadata
        return song

    def calculate_beats(self):
        beats = []
        current_time = 0
        last_note = max([c.notes[-1] for c in self.charts])
        bpm_events = self.events_by_type(BPMChangeTickEvent)
        bpm_events.append(BPMChangeTickEvent(last_note.time, last_note.tick, bpm_events[-1].new_bpm))
        current_id = 0
        for current_bpm_event, next_bpm_event in zip(bpm_events[:-1], bpm_events[1:]):
            current_beat = 0
            ts: TSEvent = [t for t in self.events_by_type(TSEvent) if t.time <= current_time][-1]
            ts_num, ts_denom = ts.numerator, ts.denominator
            seconds_per_beat = (1 / (current_bpm_event.new_bpm / 60)) / ts_denom
            while current_time < next_bpm_event.time:
                beats.append(BeatEvent(current_time, current_id, current_id, True if current_beat % ts_num == 0 else False))
                current_time += seconds_per_beat
                current_beat += 1
        self.events.extend(beats)

    def process_lyrics(self):
        """Takes a Song and generates a LyricAnimator-compatible list of LyricEvents."""
        end_time = None
        current_full_string = ""
        unprocessed_lyrics: list[LyricEvent] = []
        processsed_lyrics: list[LyricEvent] = []
        self.events = cast("list[TickEvent]", self.events)
        for e in self.events:
            if isinstance(e, TextEvent):
                if e.text == "phrase_start" or "phrase_end":
                    if e.text == "phrase_start":
                        end_time = None
                    if unprocessed_lyrics:
                        for ee in unprocessed_lyrics:
                            ee.end_time = e.time if end_time is None else end_time
                            ee.text = current_full_string
                        processsed_lyrics.extend(unprocessed_lyrics)
                        unprocessed_lyrics = []
                        current_full_string = ""
            if isinstance(e, RawLyricEvent):
                text = e.text.strip()
                for c in ["+", "#", "^", "*", "%", "$", "/"]:
                    text = text.replace(c, "")
                if text.endswith("-"):
                    text = text.removesuffix("-")
                elif text.endswith("="):
                    text = text.removesuffix("=") + "-"
                else:
                    text = text + " "
                text = text.replace("=", "-")
                text = text.replace("§", "_")
                text = re.sub("<.+>", "", text)  # TODO: Get formatting working for real.
                current_full_string += text
                unprocessed_lyrics.append(LyricEvent(e.time, 0, "", karaoke = current_full_string))
        for p in processsed_lyrics:
            p.text = nuke_smart_quotes(p.text)
            p.karaoke = nuke_smart_quotes(p.karaoke)
        self.lyrics = processsed_lyrics

    def index(self):
        """Save indexes of important look-up events. THIS IS SLOW."""
        self.indexes_by_tick["bpm"] = Index[Ticks, BPMChangeTickEvent](self.events_by_type(BPMChangeTickEvent), "tick")
        self.indexes_by_tick["time_sig"] = Index[Ticks, TSEvent](self.events_by_type(TSEvent), "tick")
        self.indexes_by_tick["section"] = Index[Ticks, SectionEvent](self.events_by_type(SectionEvent), "tick")

        self.indexes_by_time["bpm"] = Index[Seconds, BPMChangeTickEvent](self.events_by_type(BPMChangeTickEvent), "time")
        self.indexes_by_time["time_sig"] = Index[Seconds, TSEvent](self.events_by_type(TSEvent), "time")
        self.indexes_by_time["section"] = Index[Seconds, SectionEvent](self.events_by_type(SectionEvent), "time")
        self.indexes_by_time["beat"] = Index[Seconds, BeatEvent](self.events_by_type(BeatEvent), "time")

# SKIN
@cache
def load_note_texture(note_type, note_lane, height) -> Texture:
    image_name = f"{note_type}-{note_lane + 1}"
    open_height = int(height / (128 / 48))
    try:
        image = img_from_path(files(skins) / "hero" / f"{image_name}.png")
        if image.height != height and note_lane != 7:
            width = int((height / image.height) * image.width)
            image = image.resize((width, height), PIL.Image.LANCZOS)
        elif image.height != open_height:
            width = int((open_height / image.height) * image.width)
            image = image.resize((width, open_height), PIL.Image.LANCZOS)
    except Exception as e:
        logger.error(f"Unable to load texture: {image_name} | {e}")
        return load_missing_texture(height, height)
    return Texture(image)


class HeroNoteSprite(Sprite):
    def __init__(self, note: HeroNote, highway: HeroHighway, height = 128, *args, **kwargs):
        self.note: HeroNote = note
        self.highway: HeroHighway = highway
        tex = load_note_texture(note.type, note.lane, height)
        super().__init__(tex, *args, **kwargs)

    def __lt__(self, other: HeroNoteSprite):
        return self.note.time < other.note.time

    def update_animation(self, delta_time: float) -> None:
        if self.highway.auto:
            if self.highway.song_time >= self.note.time:
                self.note.hit = True
        elif self.note.hit:
            self.alpha = 0


# TODO: Remove redundant LongNoteRenderer code as it has been depreciated

class HeroLongNoteSprites(LongNoteRenderer):
    def __init__(self, note: HeroNote, highway: "HeroHighway", height=128, *args, **kwargs):
        cap_texture = load_note_texture('cap', note.lane, 64)
        cap_missed = load_note_texture('cap', 5, 64)
        body_texture = load_note_texture('body', note.lane, 128)
        body_missed = load_note_texture('body', 5, 128)
        tail_texture = load_note_texture('tail', note.lane, 128)
        tail_missed = load_note_texture('tail', 5, 128)

        # Notes are positioned based on top left, so we have to shift down to the center
        x = highway.lane_x(note.lane) + highway.note_size*0.5
        y = highway.note_y(note.time) - highway.note_size*0.5

        super().__init__(cap_texture, body_texture, tail_texture, highway.note_size, height, x, y,
                         cap_missed, body_missed, tail_missed)
        global note_id  # TODO: globals suck, is there a way to store this on the class?
        note_id += 1
        self.id = note_id

        self.note = note

    def update_animation(self, delta_time: float) -> None:
        raise NotImplementedError("Currently Long Notes don't support animations")


# TODO: Merge this with the nearly identical code in four_key.py

class NoteSprite(Sprite):

    def __init__(self, x: float, y: float):
        super().__init__(center_x=x, center_y=y)
        self.note = None


class SustainTextureSet(NamedTuple):
    tail_primary: Texture
    body_primary: Texture
    cap_primary: Texture
    tail_miss: Texture = None
    body_miss: Texture = None
    cap_miss: Texture = None
    tail_hit: Texture = None
    body_hit: Texture = None
    cap_hit: Texture = None


class SustainNote:

    def __init__(self, size, tail_spacing: float = 0.0, down_scrolling: bool = False):
        self.size = size
        self.down_scrolling: bool = down_scrolling

        self._cap: Sprite = Sprite(center_x=-1000)
        self._body: Sprite = Sprite(center_x=-1000)
        self._tail: Sprite = Sprite(center_x=-1000)

        self._tail_spacing: float = tail_spacing
        self._body_offset: float = 0.0
        self._cap_offset: float = 0.0

        self.note: Note = None
        self._textures: SustainTextureSet = None

        self.hide()

    def get_sprites(self):
        return self._cap, self._body, self._tail

    def place(self, note: Note, x, y, length, textures):
        self.note = note
        self._textures = textures
        self.update_texture()

        body_size = length - textures.cap_primary.height - self._tail_spacing
        self._body_offset = body_size / 2.0 + self._tail_spacing
        self._cap_offset = length - textures.cap_primary.height / 2.0

        if self.down_scrolling:
            self._body_offset *= -1
            self._cap_offset *= -1

        self._tail.position = x, y
        self._body.position = x, y - self._body_offset
        self._body.height = body_size
        self._cap.position = x, y - self._cap_offset

        self.show()

    def set_y(self, y):
        self._tail.center_y = y
        self._body.center_y = y - self._body_offset
        self._cap.center_y = y - self._cap_offset

    def show(self):
        self._cap.visible = True
        self._body.visible = True
        self._tail.visible = True

    def hide(self):
        self._cap.visible = False
        self._body.visible = False
        self._tail.visible = False

    def update_texture(self):
        if not self.note or not self._textures:
            return

        t = self._textures

        if self.note.missed:
            self._tail.texture = t.tail_miss or t.tail_primary
            self._body.texture = t.body_miss or t.body_primary
            self._cap.texture = t.cap_miss or t.cap_primary
        elif self.note.hit:
            self._tail.texture = t.tail_hit or t.tail_primary
            self._body.texture = t.body_hit or t.body_primary
            self._cap.texture = t.cap_hit or t.cap_primary
        else:
            self._tail.texture = t.tail_primary
            self._body.texture = t.body_primary
            self._cap.texture = t.cap_primary


class HeroHighway(Highway):
    def __init__(self, chart: HeroChart, pos: tuple[int, int], size: tuple[int, int] = None, gap: int = 5, auto = False, show_flags = False):
        if size is None:
            self.window = arcade.get_window()
            size = int(self.window.width / (1280 / 400)), self.window.height

        super().__init__(chart, pos, size, gap, downscroll = True)

        self.perp_static = PerspectiveProjector()

        self.view_angle = 70.0
        self.view_dist = 400.0

        data = self.perp_static.view
        data_h_fov = 0.5 * self.perp_static.projection.fov
        self.perp_static.projection.far = 10000.0

        look_radians = math.radians(self.view_angle - data_h_fov)

        self.perp_y_pos = -self.view_dist * math.sin(look_radians)
        self.perp_z_pos = self.view_dist * math.cos(look_radians)

        data.position = (self.window.center_x, self.perp_y_pos, self.perp_z_pos)
        data.up, data.forward = arcade.camera.grips.rotate_around_right(data, -self.view_angle)

        self.perp_moving = PerspectiveProjector(
            view=duplicate_camera_data(data),
            projection=self.perp_static.projection
        )

        self.chart: HeroChart = self.chart

        self.viewport = 0.75  # TODO: Set dynamically.

        # NOTE POOL DEFINITION AND CONSTRUCTION

        # Generators are great for ease, but it means we can't really 'scrub' backwards through the song
        # So this is a patch job at best.
        self._note_generator: Generator[Note, Any, None] = (note for note in self.notes)

        self._note_pool: Pool[NoteSprite] = Pool(
            list(NoteSprite(x=-1000.0, y=-1000.0) for _ in range(1000))
        )
        self._note_sprites: SpriteList[NoteSprite] = SpriteList(capacity=1024)
        self._note_sprites.program = self.window.ctx.sprite_list_program_no_cull  # avoid orthographic culling
        self._note_sprites.extend(self._note_pool.source)

        self._next_note: HeroNote = next(self._note_generator, None)

        # SUSTAIN POOL DEFINITION AND CONSTRUCTION

        # Generators are great for ease, but it means we can't really 'scrub' backwards through the song
        # So this is a patch job at best.
        self._sustain_generator: Generator[Note, Any, None] = (note for note in self.notes if note.length)

        self._sustain_pool: Pool[SustainNote] = Pool(
            list(SustainNote(self.note_size, self.note_size/2.0, True) for _ in range(100))
        )
        self._sustain_sprites: SpriteList[Sprite] = SpriteList()
        self._sustain_sprites.program = self.window.ctx.sprite_list_program_no_cull  # avoid orthographic culling
        for sustain in self._sustain_pool.source:
            self._sustain_sprites.extend(sustain.get_sprites())

        _missed_tail = load_note_texture('tail', 5, self.note_size)
        _missed_body = load_note_texture('body', 5, self.note_size)
        _missed_cap = load_note_texture('cap', 5, self.note_size // 2)

        self._sustain_textures = {
            0: SustainTextureSet(load_note_texture('tail', 0, self.note_size),
                                 load_note_texture('body', 0, self.note_size),
                                 load_note_texture('cap', 0, self.note_size // 2),
                                 _missed_tail, _missed_body, _missed_cap),
            1: SustainTextureSet(load_note_texture('tail', 1, self.note_size),
                                 load_note_texture('body', 1, self.note_size),
                                 load_note_texture('cap', 1, self.note_size // 2),
                                 _missed_tail, _missed_body, _missed_cap),
            2: SustainTextureSet(load_note_texture('tail', 2, self.note_size),
                                 load_note_texture('body', 2, self.note_size),
                                 load_note_texture('cap', 2, self.note_size // 2),
                                 _missed_tail, _missed_body, _missed_cap),
            3: SustainTextureSet(load_note_texture('tail', 3, self.note_size),
                                 load_note_texture('body', 3, self.note_size),
                                 load_note_texture('cap', 3, self.note_size // 2),
                                 _missed_tail, _missed_body, _missed_cap),
            4: SustainTextureSet(load_note_texture('tail', 4, self.note_size),
                                 load_note_texture('body', 4, self.note_size),
                                 load_note_texture('cap', 4, self.note_size // 2),
                                 _missed_tail, _missed_body, _missed_cap)
        }

        self._next_sustain = next(self._sustain_generator, None)

        self.auto = auto

        self._show_flags = show_flags

        self.color = (0, 0, 0, 128)  # TODO: eventually this will be a scrolling image.

        self.strikeline = SpriteList()
        self.strikeline.program = self.strikeline.ctx.sprite_list_program_no_cull
        # TODO: Is this dumb?
        for i in range(5):
            sprite = HeroNoteSprite(HeroNote(self.chart, 0, i, 0, "strikeline"), self, self.note_size)
            sprite.top = self.strikeline_y
            sprite.left = self.lane_x(sprite.note.lane)
            sprite.alpha = 128
            self.strikeline.append(sprite)

        self._last_strikeline_note: list[HeroNote] = [None] * 5

        logger.debug(f"Generated highway for chart {chart.instrument}.")

        # TODO: Replace with better pixel_offset calculation or remove entirely
        self.last_update_time = 0
        self._pixel_offset = 0

    def update(self, song_time: float) -> None:
        super().update(song_time)

        while self._next_note is not None and self._next_note.time <= (self.song_time + self.viewport) and self._note_pool.has_free_slot():
            note = self._next_note
            sprite = self._note_pool.get()
            sprite.texture = load_note_texture(note.type, note.lane, self.note_size)
            sprite.position = self.lane_x(note.lane) + sprite.width/2, self.note_y(note.time) - sprite.height/2.0
            sprite.visible = True
            sprite.note = note

            self._next_note = next(self._note_generator, None)
            # Filters out the flags if they aren't supposed to be shown
            while self._next_note and (self._next_note.lane in {5, 6}) and not self._show_flags:
                self._next_note = next(self._note_generator, None)

        while self._next_sustain is not None and self._next_sustain.time <= (self.song_time + self.viewport) and self._sustain_pool.has_free_slot():
            note = self._next_sustain
            sustain = self._sustain_pool.get()
            sustain.place(
                note,
                self.lane_x(self._next_sustain.lane) + sustain.size/2.0,
                self.note_y(note.time) - sustain.size/2.0,
                note.length * self.px_per_s,
                self._sustain_textures[note.lane]
            )

            self._next_sustain = next(self._sustain_generator, None)

        for sprite in self._note_pool.given_items:
            sprite.center_y = self.note_y(sprite.note.time) - sprite.height/2.0
            if sprite.note.hit or sprite.note.time <= (song_time - 0.1):
                sprite.visible = False
                self._note_pool.give(sprite)

        for sustain in self._sustain_pool.given_items:
            sustain.set_y(self.note_y(sustain.note.time) - sustain.size/2.0)
            sustain.update_texture()
            if sustain.note.end <= (song_time - 0.1):
                sustain.hide()
                self._sustain_pool.give(sustain)

        # TODO: Remove auto features from Highway and Engine and use an auto-input instead

        # if self.auto:
        #     # while self.note_sprites[self.note_index].note.time < self.song_time - 0.050:
        #     #     self.note_index += 1
        #     # Fancy strikeline
        #     i = self.chart.indexes_by_time["note"].lteq_index(self.song_time - 0.050) or 0
        #     while True:
        #         note_sprite = self.note_sprites[i]
        #         if note_sprite.note.time > self.song_time + 0.050:
        #             break
        #         if note_sprite.note.lane < 5:
        #             self._last_strikeline_note[note_sprite.note.lane] = note_sprite.note
        #         if self.song_time > note_sprite.note.time:
        #             note_sprite.alpha = 0
        #         i += 1
        #     for n, note in enumerate(self._last_strikeline_note):
        #         if note is None:
        #             self.strikeline[n].alpha = 64
        #         else:
        #             self.strikeline[n].alpha = ease_linear(255, 64, perc(note.end, note.end + 0.25, self.song_time))


    @property
    def pos(self) -> tuple[int, int]:
        return self._pos

    @pos.setter
    def pos(self, p: tuple[int, int]) -> None:
        old_pos = self._pos
        diff_x = p[0] - old_pos[0]
        diff_y = p[1] - old_pos[1]
        self._pos = p
        self.strikeline.move(diff_x, diff_y)

    @property
    def pixel_offset(self) -> int:
        # TODO: Replace with better pixel_offset calculation
        return self._pixel_offset

    def draw(self) -> None:
        self.window.ctx.blend_func = self.window.ctx.BLEND_DEFAULT
        with self.perp_static.activate():
            arcade.draw_lrbt_rectangle_filled(self.x, self.x + self.w,
                                              self.y, self.y + self.h,
                                              self.color)
            current_beat_idx = self.chart.song.indexes_by_time["beat"].lteq_index(self.song_time)
            last_beat_idx = self.chart.song.indexes_by_time["beat"].lteq_index(self.song_time + self.viewport)
            for beat in self.chart.song.events_by_type(BeatEvent)[current_beat_idx:last_beat_idx + 1]:
                px = self.note_y(beat.time) - (self.note_size / 2)
                arcade.draw_line(self.x, px, self.x + self.w, px, colors.DARK_GRAY, 3 if beat.major else 1)

            self.strikeline.draw()

            self._sustain_sprites.draw()
            self._note_sprites.draw()

    def lane_x(self, lane_num: int) -> int:
        if lane_num == 7:  # tap note override
            return self.x
        return (self.note_size + self.gap) * lane_num + self.x

    @property
    def show_flags(self) -> bool:
        return self._show_flags

    @show_flags.setter
    def show_flags(self, v: bool) -> None:
        self._show_flags = v
        # TODO: Remove? Unsure what this did
        # if self._show_flags:
        #     for sprite in self.sprite_buckets.sprites:
        #         if sprite.note.lane in [5, 6]:
        #             sprite.alpha = 255
        # else:
        #     for sprite in self.sprite_buckets.sprites:
        #         if sprite.note.lane in [5, 6]:
        #             sprite.alpha = 0


@dataclass
class StrumEvent(Event):
    action: Action
    shape: list[bool]

    def __str__(self) -> str:
        strum_name = {
            keymap.hero.strumup: "up",
            keymap.hero.strumup: "down"
        }
        return f"<StrumEvent {strum_name[self.action]} @ {round(self.time, 3)}: {[n for n, v in enumerate(self.shape) if v is True]}>"


FRET_ACTIONS = (keymap.hero.green, keymap.hero.red, keymap.hero.yellow, keymap.hero.blue, keymap.hero.orange)
STRUM_ACTIONS = (keymap.hero.strumup, keymap.hero.strumdown)
POWER_ACTIONS = (keymap.hero.power,)

class HeroEngine(Engine):
    def __init__(self, chart: Chart, offset: Seconds = 0):
        hit_window = 0.050  # 50ms +/-
        judgements = [Judgement("pass", 50, 100, 1, 1), Judgement("miss", math.inf, 0, 0, -1)]

        super().__init__(chart, hit_window, judgements, offset)

        self.current_chords: list[HeroChord] = self.chart.chords.copy()
        self.current_events: list[DigitalKeyEvent[Literal[0,1,2,3,4,5,6,7]]] = []

        self.combo = 0
        self.star_power = False
        self.strum_events: list[StrumEvent] = []

        self.tap_available = True

    @property
    def current_holds(self) -> list[bool]:
        return keymap.hero.state

    @property
    def multiplier(self) -> int:
        base = min(((self.combo // 10) + 1), 4)
        return base * 2 if self.star_power else base

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        # ignore spam during front/back porch
        if (self.chart_time < self.chart.notes[0].time - self.hit_window
           or self.chart_time > self.chart.notes[-1].time + self.hit_window):
            return
        action = keymap.hero.pressed_action
        if action is None:
            return
        # pressed
        key = cast(Literal[0,1,2,3,4,5,6,7], keymap.hero.actions.index(action))
        self.current_events.append(DigitalKeyEvent(self.chart_time, key, "down"))
        if action in FRET_ACTIONS:
            # fret button
            self.tap_available = True
        elif action in STRUM_ACTIONS:
            # strum button
            self.strum_events.append(StrumEvent(self.chart_time, action, self.current_holds))
        elif action in POWER_ACTIONS:
            # power button
            pass

    def on_key_release(self, symbol: int, modifiers: int) -> None:
        # ignore spam during front/back porch
        if (self.chart_time < self.chart.notes[0].time - self.hit_window
           or self.chart_time > self.chart.notes[-1].time + self.hit_window):
            return
        action = keymap.hero.released_action
        if action is None:
            return
        key = cast(Literal[0,1,2,3,4,5,6,7], keymap.hero.actions.index(action))
        self.current_events.append(DigitalKeyEvent(self.chart_time, key, "up"))
        if action in FRET_ACTIONS:
            # fret button
            self.tap_available = True

    def calculate_score(self) -> None:
        # CURRENTLY MISSING:
        # Sutains
        # Sustain drops
        # Overstrums
        # Strum leniency

        # Get all non-scored notes within the current window
        look_at_chords = [c for c in self.current_chords if c.time <= self.chart_time + self.hit_window]
        look_at_strums = [e for e in self.strum_events if self.chart_time - self.hit_window <= e.time <= self.chart_time + self.hit_window]

        for chord in look_at_chords:
            # Strums or HOPOs in strum mode
            if chord.type == "normal" or (chord.type == "hopo" and self.combo == 0):
                self.process_strum(chord, look_at_strums)
            elif chord.type == "hopo" or chord.type == "tap":
                self.process_tap(chord, look_at_strums)

        # Missed chords
        missed_chords = [c for c in self.current_chords if self.chart_time > c.time + self.hit_window]
        for chord in missed_chords:
            self.process_missed(chord)

        overstrums = [e for e in self.strum_events if self.chart_time > e.time + self.hit_window]
        if overstrums:
            print(f"Overstrum! ({round(overstrums[0].time, 3)})")
            self.combo = 0
            for o in overstrums:
                self.strum_events.remove(o)

    def process_strum(self, chord: HeroChord, strum_events: list[StrumEvent]) -> None:
        for event in strum_events:
            if event.shape in chord.valid_shapes:
                chord.hit = True
                chord.hit_time = event.time
                self.score_chord(chord)
                self.current_chords.remove(chord)
                self.strum_events.remove(event)

    def process_tap(self, chord: HeroChord, strum_events: list[StrumEvent]) -> None:
        if self.current_holds in chord.valid_shapes and self.tap_available:
            chord.hit = True
            chord.hit_time = self.chart_time
            self.score_chord(chord)
            self.current_chords.remove(chord)
            self.tap_available = False
        else:
            self.process_strum(chord, strum_events)

    def process_missed(self, chord: HeroChord) -> None:
        chord.missed = True
        chord.hit_time = math.inf
        self.score_chord(chord)
        self.current_chords.remove(chord)

    def score_chord(self, chord: HeroChord) -> None:
        if chord.hit:
            self.score += 50 * self.multiplier
            self.combo += 1
        elif chord.missed:
            self.combo = 0
