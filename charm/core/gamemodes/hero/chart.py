from __future__ import annotations

from collections.abc import Sequence
from typing import NamedTuple
from enum import StrEnum
from dataclasses import dataclass
from nindex.index import Index

from charm.core.generic import Chart, Event, Note, ChartMetadata
from charm.lib.errors import ThisShouldNeverHappenError
from charm.lib.types import Seconds

Ticks = int


class HeroNoteType(StrEnum):
    STRUM = "strum"
    HOPO = "hopo"
    TAP = "tap"
    FORCED = "force"


class ChordShape(NamedTuple):
    green: bool | None
    red: bool | None
    yellow: bool | None
    blue: bool | None
    orange: bool | None

    def __repr__(self) -> str:
        return (f"<ChordShape {'G' if self.green else '_' if self.green is not None else 'X'}"
                            f"{'R' if self.red else '_' if self.red is not None else 'X'}"
                            f"{'Y' if self.yellow else '_' if self.yellow is not None else 'X'}"
                            f"{'B' if self.blue else '_' if self.blue is not None else 'X'}"
                            f"{'O' if self.orange else '_' if self.orange is not None else 'X'}>")

    def is_compatible(self, other: ChordShape) -> bool:
        for fret in ("green", "red", "yellow", "blue", "orange"):
            self_fret = getattr(self, fret)
            other_fret = getattr(other, fret)
            if self_fret is None or other_fret is None:
                # None means this fret can be anchored, so either False or True are fine
                continue
            if self_fret != other_fret:
                return False
        return True


@dataclass
class HeroNote(Note["HeroChart", HeroNoteType]):
    def __init__(self, chart: HeroChart, time: Seconds, lane: int, length: Seconds, type: HeroNoteType, tick: Ticks, tick_length: Ticks):
        super().__init__(chart, time, lane, length, type)
        self.tick: Ticks = tick
        self.tick_length: Ticks = tick_length


class HeroChord:
    """A data object to hold notes and have useful functions for manipulating and reading them."""
    def __init__(self, notes: list[HeroNote] | None = None) -> None:
        self.notes = notes if notes else []

    @property
    def frets(self) -> tuple[int, ...]:
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
    def shape(self) -> ChordShape:
        # ! THIS IS VERY UNROLLED DRAGON PLS HELP
        if 7 in self.frets:
            return ChordShape(False, False, False, False, False)
        if len(self.frets) == 1:
            # Single notes
            match self.notes[0].lane:
                case 0:
                    return ChordShape(True,  False, False, False, False)
                case 1:
                    return ChordShape(None,  True,  False, False, False)
                case 2:
                    return ChordShape(None,  None,  True,  False, False)
                case 3:
                    return ChordShape(None,  None,  None,  True,  False)
                case 4:
                    return ChordShape(None,  None,  None,  None,  True)
                case _:
                    raise ThisShouldNeverHappenError
        else:
            # Chords
            min_fret = min(*self.frets)
            lanes: list[bool | None] = [None, None, None, None, None]
            for i in range(5):
                if i < min_fret:
                    if self.type == HeroNoteType.TAP:
                        # You can anchor taps in CH, so I'm rolling with it for now.
                        lanes[i] = None
                    else:
                        lanes[i] = False
                else:
                    lanes[i] = i in self.frets
            return ChordShape(*lanes)


@dataclass
class TickEvent(Event):
    tick: int


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


class HeroNIndexCollection(NamedTuple):
    bpm_time: Index[Seconds, BPMChangeTickEvent]
    bpm_tick: Index[Ticks, BPMChangeTickEvent]
    time_sig_time: Index[Seconds, TSEvent]
    time_sig_tick: Index[Ticks, TSEvent]
    section_time: Index[Seconds, SectionEvent]
    section_tick: Index[Ticks, SectionEvent]
    beat_time: Index[Seconds, BeatEvent]
    note_time: Index[Seconds, HeroNote]
    note_tick: Index[Ticks, HeroNote]
    chord_time: Index[Seconds, HeroChord]
    chort_tick: Index[Ticks, HeroChord]


class HeroChart(Chart[HeroNote]):
    def __init__(self, metadata: ChartMetadata, notes: Sequence[HeroNote], events: Sequence[Event]) -> None:
        super().__init__(metadata, notes, events)
        self.chords: list[HeroChord] = []
        self.indices: HeroNIndexCollection

    def calculate_indices(self) -> None:
        # !: This assumes that the events, notes, and chords are all time sorted :3
        bpm = self.events_by_type(BPMChangeTickEvent)
        ts = self.events_by_type(TSEvent)
        section = self.events_by_type(SectionEvent)
        beat = self.events_by_type(BeatEvent)
        note = self.notes
        chord = self.chords
        self.indices = HeroNIndexCollection(
            Index[Seconds, BPMChangeTickEvent](bpm, 'time'),
            Index[Ticks, BPMChangeTickEvent](bpm, 'tick'),
            Index[Seconds, TSEvent](ts, 'time'),
            Index[Ticks, TSEvent](ts, 'tick'),
            Index[Seconds, SectionEvent](section, 'time'),
            Index[Ticks, SectionEvent](section, 'tick'),
            Index[Seconds, BeatEvent](beat, 'time'),
            Index[Seconds, HeroNote](note, 'time'),
            Index[Ticks, HeroNote](note, 'tick'),
            Index[Seconds, HeroChord](chord, 'time'),
            Index[Ticks, HeroChord](chord, 'tick')
        )
