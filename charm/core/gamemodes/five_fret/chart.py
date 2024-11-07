from __future__ import annotations

from collections.abc import Sequence
from typing import NamedTuple
from enum import StrEnum, IntEnum
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


class Fret(IntEnum):
    GREEN = 0
    RED = 1
    YELLOW = 2
    BLUE = 3
    ORANGE = 4


class ChordShape(NamedTuple):
    green: bool | None
    red: bool | None
    yellow: bool | None
    blue: bool | None
    orange: bool | None

    def __repr__(self) -> str:
        return (
            f"<ChordShape {'G' if self.green else ('X' if self.green is None else '_')}"
            f"{'R' if self.red else ('X' if self.red is None else '_')}"
            f"{'Y' if self.yellow else ('X' if self.yellow is None else '_')}"
            f"{'B' if self.blue else ('X' if self.blue is None else '_')}"
            f"{'O' if self.orange else ('X' if self.orange is None else '_')}>"
        )
    

    def matches(self, other: ChordShape) -> bool:
        for a, b in zip(self, other, strict=True):
            if a is None or b is None:
                # None means this fret can be anchored, so either False or True are fine
                continue
            if a != b:
                return False
        return True
    
    def contains(self, other: ChordShape) -> bool:
        for a, b in zip(self, other, strict=True):
            if a is None or b is None:
                # None means this fret can be anchored, so either False or True are fine
                continue
            if (not a) and b:
                return False
        return False

    @property
    def is_open(self) -> bool:
        return not any(self)

    @classmethod
    def from_fret(cls, fret: Fret) -> ChordShape:
        return cls(
                fret == Fret.GREEN,
                fret == Fret.RED,
                fret == Fret.YELLOW,
                fret == Fret.BLUE,
                fret == Fret.ORANGE,
            )

    def update_fret(self, fret: int, state: bool) -> ChordShape:
        f = list(self)
        f[fret] = state
        return ChordShape(*f)

    def __and__(self, other: ChordShape) -> ChordShape:
        return ChordShape(
            None if (self.green is None or other.green is None) else self.green and other.green,
            None if (self.red is None or other.red is None) else self.red and other.red,
            None if (self.yellow is None or other.yellow is None) else self.yellow and other.yellow,
            None if (self.blue is None or other.blue is None) else self.blue and other.blue,
            None if (self.orange is None or other.orange is None) else self.orange and other.orange,
        )

    def __or__(self, other: ChordShape) -> ChordShape:
        return ChordShape(self.green or other.green, self.red or other.red, self.yellow or other.yellow, self.blue or other.blue, self.orange or other.orange)


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
        self.frets: list[int] = sorted(set(n.lane for n in self.notes))
        self.size: int = len(self.frets)

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
    def disjoint(self) -> bool:
        return not (
            len(self.notes) != 1
            and
            all(self.notes[0].length == note.length for note in self.notes)
        )

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
        # Chords
        fret_set = set(self.frets)
        is_anchored = self.type == FiveFretNoteType.TAP or len(self.frets) == 1
        min_fret = min(fret_set)
        return ChordShape(
            *(
                None if (i < min_fret and is_anchored) else i in fret_set
                for i in range(5)
            )
        )


class FiveFretSustain(FiveFretChord):
    pass


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
        resolution: int = 192
    ) -> None:
        super().__init__(metadata, notes, events)
        self.chords: list[FiveFretChord] = []
        self.indices: FiveFretNIndexCollection
        self.resolution: int = resolution

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
