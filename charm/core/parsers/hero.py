from __future__ import annotations

import configparser
from collections import defaultdict
from collections.abc import Sequence
import itertools
import logging
from pathlib import Path
import re
from nindex import Index

from charm.lib.errors import MetadataParseError, NoChartsError, NoMetadataError, ChartParseError, ChartPostReadParseError
from charm.lib.types import Seconds
from charm.lib.utils import nuke_smart_quotes
from charm.core.gamemodes.five_fret import (
    FiveFretChart,
    FiveFretNote,
    FiveFretChord,
    Ticks,
    BPMChangeTickEvent,
    TextEvent,
    SoloEvent,
    TSEvent,
    SectionEvent,
    RawLyricEvent,
    StarpowerEvent,
    BeatEvent,
    FiveFretNoteType
)
from charm.objects.lyric_animator import LyricEvent

from charm.core.generic import ChartMetadata, ChartSetMetadata, Parser

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
    bpm_events = sorted(b for b in sync_track if b.tick <= current_tick)
    bpm_events.sort(key=lambda x: x.tick)
    last_bpm_event = bpm_events[-1]
    tick_delta = current_tick - last_bpm_event.tick
    bps = last_bpm_event.new_bpm / 60
    seconds = tick_delta / (resolution * bps)
    return seconds + offset + last_bpm_event.time


def process_chart_lyric_events(chart: FiveFretChart) -> None:
    """Takes a Song and generates a LyricAnimator-compatible list of LyricEvents."""
    end_time = None
    current_full_string = ""
    unprocessed_lyrics: list[LyricEvent] = []
    processsed_lyrics: list[LyricEvent] = []
    for e in chart.events:
        if isinstance(e, TextEvent):
            if e.text == "phrase_start" or "phrase_end":
                if e.text == "phrase_start":
                    end_time = None
                if unprocessed_lyrics:
                    for unprocessed_lyric in unprocessed_lyrics:
                        unprocessed_lyric.end_time = e.time if end_time is None else end_time
                        unprocessed_lyric.text = current_full_string
                    processsed_lyrics.extend(unprocessed_lyrics)
                    unprocessed_lyrics = []
                    current_full_string = ""
        elif isinstance(e, RawLyricEvent):
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
    chart.events.extend(processsed_lyrics)


def create_chart_chords(chart: FiveFretChart) -> None:
    """
    Turn lists of notes (in `self.notes`) into `HeroChord`s (in `self.chords`)
    A chord is defined as all notes occuring at the same tick.
    While this could be a method on HeroChart I am keeping it
    seperate to keep parsing of hero charts all in one file ~Dragon
    """
    c: dict[Ticks, list[FiveFretNote]] = defaultdict(list[FiveFretNote])
    for note in chart.notes:
        c[note.tick].append(note)
    chord_lists = list(c.values())
    chords: list[FiveFretChord] = []
    for cl in chord_lists:
        chords.append(FiveFretChord(cl))
    chart.chords = chords


def calculate_chart_note_flags(chart: FiveFretChart) -> None:
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
                n.type = FiveFretNoteType.TAP
            elif forced:
                n.type = FiveFretNoteType.FORCED
        c.notes = [n for n in c.notes if n.lane not in {5, 6}]


def parse_chart_text_events(chart: FiveFretChart) -> None:
    current_solo = None
    for e in chart.events_by_type(TextEvent):
        if e.text == "solo":
            current_solo = e
            chart.events.remove(e)
        elif e.text == "soloend":
            if current_solo is None:
                raise ChartPostReadParseError("`solo_end` without `solo` event!")
            tick_length = e.tick - current_solo.tick
            length = e.time - current_solo.time
            chart.events.append(SoloEvent(current_solo.time, current_solo.tick, tick_length, length))
            current_solo = None
            chart.events.remove(e)


def calculate_chart_hopos(chart: FiveFretChart, time_sig_ticks: Index[Ticks, TSEvent], resolution: float) -> None:
            # This is basically ripped from Charm-Legacy.
        # https://github.com/DigiDuncan/Charm-Legacy/blob/3187a8f2fa8c8876c2706b731bff6913dc0bad60/charm/song.py#L179
        for last_chord, current_chord in zip(chart.chords[:-1], chart.chords[1:], strict = True):  # python zip pattern, wee
            timesig = time_sig_ticks.lteq(last_chord.tick)
            if timesig is None:
                timesig = TSEvent(0, 0, 4, 4)

            ticks_per_quarternote = resolution
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


def create_chart_beat_events(chart: FiveFretChart, time_sig_seconds: Index[Seconds, TSEvent]) -> None:
    beats: list[BeatEvent] = []
    current_time = 0
    last_note = chart.notes[-1]
    bpm_events = chart.events_by_type(BPMChangeTickEvent)
    bpm_events.append(BPMChangeTickEvent(last_note.time, last_note.tick, bpm_events[-1].new_bpm))
    current_id = 0
    for current_bpm_event, next_bpm_event in itertools.pairwise(bpm_events):
        current_beat = 0
        ts: TSEvent = time_sig_seconds.lteq(current_time)
        ts_num, ts_denom = ts.numerator, ts.denominator
        seconds_per_beat = (1 / (current_bpm_event.new_bpm / 60)) / ts_denom
        while current_time < next_bpm_event.time:
            beats.append(BeatEvent(current_time, current_id, current_id, True if current_beat % ts_num == 0 else False))
            current_time += seconds_per_beat
            current_beat += 1
    chart.events.extend(beats)


class HeroParser(Parser):
    gamemode = "hero"

    @staticmethod
    def is_possible_chartset(path: Path) -> bool:
        """Does this folder contain a parseable ChartSet?"""
        return len(tuple(path.glob('./*.chart'))) > 0

    @staticmethod
    def is_parsable_chart(path: Path) -> bool:
        """Is this chart parsable by this Parser"""
        return path.name == 'notes.chart'

    @staticmethod
    def parse_chartset_metadata(path: Path) -> ChartSetMetadata:
        if not (path / "song.ini").exists():
            raise NoMetadataError(path.stem)
        parser = configparser.ConfigParser(interpolation = None)
        parser.read((path / "song.ini").absolute(), encoding = "utf-8")
        if "song" not in parser and "Song" not in parser:
            raise MetadataParseError("Song header not found in metadata!")
        song_header = "song" if "song" in parser else "Song"
        song = parser[song_header]

        try:
            length = song.getfloat("song_length") / 1000
        except (ValueError, TypeError):
            length = None

        try:
            year = song.getint("year")
        except ValueError:
            year = None

        return ChartSetMetadata(
            path=path,
            title=song.get("name", None),
            artist=song.get("artist", None),
            album=song.get("album", None),
            length=length,
            genre=song.get("genre", None),
            year=year,
            charter=song.get("charter", None),
            gamemode="hero"
        )

    @staticmethod
    def parse_chart_metadata(path: Path) -> list[ChartMetadata]:
        metadatas: list[ChartMetadata] = []
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
                    metadatas.append(ChartMetadata("hero", diff, path / "notes.chart", inst))

        return metadatas

    @staticmethod
    def parse_chart(chart_data: ChartMetadata) -> Sequence[FiveFretChart]:
        if not (chart_data.path).exists():
            raise NoChartsError(chart_data.path.stem)
        with open(chart_data.path, encoding = "utf-8") as f:
            chartfile = f.readlines()

        target_header = f"{chart_data.difficulty}{chart_data.instrument}"
        reached_target_chart = False

        resolution: Ticks = 192
        offset: Seconds = 0

        chart = FiveFretChart(chart_data, [], [])

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
                    split = line.split('=')
                    if split[0].strip() != 'Resolution':
                        continue
                    resolution = int(split[-1].strip())
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
                        chart.notes.append(FiveFretNote(chart, seconds, int(lane), sec_length, type=FiveFretNoteType.STRUM, tick=tick, tick_length=length))  # TODO: Note flags.
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
        chart.notes.sort()
        chart.events.sort()
        process_chart_lyric_events(chart)
        create_chart_chords(chart)
        calculate_chart_note_flags(chart)
        parse_chart_text_events(chart)
        # We will recalc this later, but we don't need to sort or index the others yet so do only what we must.
        ts_events = chart.events_by_type(TSEvent)
        calculate_chart_hopos(chart, Index[Ticks, TSEvent](ts_events, "tick"), resolution)
        create_chart_beat_events(chart, Index[Seconds, TSEvent](ts_events, "time"))
        # The chart events are messed up before now. There are a bunch of sorted events with unsorted events tacked on the end
        # If this ever needs changing I am so sorry.
        chart.events.extend(HeroParser.calculate_countdowns(chart))
        chart.events.sort()
        chart.calculate_indices()
        return [chart]
