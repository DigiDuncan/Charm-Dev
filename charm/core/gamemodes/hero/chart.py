from __future__ import annotations

import itertools
from typing import NamedTuple
from dataclasses import dataclass
from enum import StrEnum
from nindex.index import Index

from charm.lib.types import Seconds

from charm.core.generic.chart import Chart, Event, Note
from charm.core.generic.metadata import ChartMetadata


Ticks = int

class HeroNoteType(StrEnum):
    STRUM = "strum"
    HOPO = "hopo"
    TAP = "tap"

@dataclass
class HeroNote(Note[HeroNoteType]):
    tick: int = None
    tick_length: Ticks = None

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

class ChartNIndexCollection(NamedTuple):
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

    def __init__(self, metadata: ChartMetadata, notes: list[HeroNote], events: list[Event]) -> None:
        super().__init__(metadata, notes, events)
        self.chords: list[HeroChord] = []
        self.indices: ChartNIndexCollection = None

    def calculate_indices(self) -> None:
        # !: This assumes that the events, notes, and chords are all time sorted :3
        bpm = self.events_by_type(BPMChangeTickEvent)
        ts = self.events_by_type(TSEvent)
        section = self.events_by_type(SectionEvent)
        beat = self.events_by_type(BeatEvent)
        note = self.notes
        chord = self.chords
        self.indices = ChartNIndexCollection(
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
