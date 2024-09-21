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


class FiveFretNoteType(StrEnum):
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
        return (
            f"<ChordShape {'G' if self.green else '_' if self.green is not None else 'X'}"
            f"{'R' if self.red else '_' if self.red is not None else 'X'}"
            f"{'Y' if self.yellow else '_' if self.yellow is not None else 'X'}"
            f"{'B' if self.blue else '_' if self.blue is not None else 'X'}"
            f"{'O' if self.orange else '_' if self.orange is not None else 'X'}>"
        )

    def is_compatible(self, other: ChordShape) -> bool:
        for a, b in zip(self, other, strict=True):
            if a is None or b is None:
                # None means this fret can be anchored, so either False or True are fine
                continue
            if a != b:
                return False
        return True


@dataclass
class FiveFretNote(Note["FiveFretChart", FiveFretNoteType]):
    def __init__(
        self,
        chart: FiveFretChart,
        time: Seconds,
        lane: int,
        length: Seconds,
        type: FiveFretNoteType,
        tick: Ticks,
        tick_length: Ticks,
    ):
        super().__init__(chart, time, lane, length, type)
        self.tick: Ticks = tick
        self.tick_length: Ticks = tick_length


class FiveFretChord:
    """A data object to hold notes and have useful functions for manipulating and reading them."""

    def __init__(self, notes: list[FiveFretNote] | None = None) -> None:
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
        if 7 in self.frets:
            # Open note
            return ChordShape(False, False, False, False, False)
        if len(self.frets) == 1:
            # Single notes
            lanes = self.notes[0].lane
            return ChordShape(
                None if 0 < lanes else 0 == lanes,  # Green
                None if 1 < lanes else 1 == lanes,  # Red
                None if 2 < lanes else 2 == lanes,  # Yellow
                None if 3 < lanes else 3 == lanes,  # Blue
                None if 4 < lanes else 4 == lanes,  # Orange
            )
        else:
            # Chords
            fret_set = set(self.frets)
            is_tap = self.type == FiveFretNoteType.TAP
            min_fret = min(*fret_set)
            return ChordShape(
                *[
                    None if (i < min_fret and is_tap) else i in fret_set
                    for i in range(5)
                ]
            )


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


class FiveFretNIndexCollection(NamedTuple):
    bpm_time: Index[Seconds, BPMChangeTickEvent]
    bpm_tick: Index[Ticks, BPMChangeTickEvent]
    time_sig_time: Index[Seconds, TSEvent]
    time_sig_tick: Index[Ticks, TSEvent]
    section_time: Index[Seconds, SectionEvent]
    section_tick: Index[Ticks, SectionEvent]
    beat_time: Index[Seconds, BeatEvent]
    note_time: Index[Seconds, FiveFretNote]
    note_tick: Index[Ticks, FiveFretNote]
    chord_time: Index[Seconds, FiveFretChord]
    chort_tick: Index[Ticks, FiveFretChord]


class FiveFretChart(Chart[FiveFretNote]):
    def __init__(
        self,
        metadata: ChartMetadata,
        notes: Sequence[FiveFretNote],
        events: Sequence[Event],
    ) -> None:
        super().__init__(metadata, notes, events)
        self.chords: list[FiveFretChord] = []
        self.indices: FiveFretNIndexCollection

    def calculate_indices(self) -> None:
        # !: This assumes that the events, notes, and chords are all time sorted :3
        bpm = self.events_by_type(BPMChangeTickEvent)
        ts = self.events_by_type(TSEvent)
        section = self.events_by_type(SectionEvent)
        beat = self.events_by_type(BeatEvent)
        note = self.notes
        chord = self.chords
        self.indices = FiveFretNIndexCollection(
            Index[Seconds, BPMChangeTickEvent](bpm, "time"),
            Index[Ticks, BPMChangeTickEvent](bpm, "tick"),
            Index[Seconds, TSEvent](ts, "time"),
            Index[Ticks, TSEvent](ts, "tick"),
            Index[Seconds, SectionEvent](section, "time"),
            Index[Ticks, SectionEvent](section, "tick"),
            Index[Seconds, BeatEvent](beat, "time"),
            Index[Seconds, FiveFretNote](note, "time"),
            Index[Ticks, FiveFretNote](note, "tick"),
            Index[Seconds, FiveFretChord](chord, "time"),
            Index[Ticks, FiveFretChord](chord, "tick"),
        )
