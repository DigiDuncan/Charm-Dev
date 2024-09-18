from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from functools import total_ordering
from typing import Any, Generic, Self, TypeVar

from charm.lib.types import Seconds

from .metadata import ChartMetadata

type BaseNote = Note[BaseChart, StrEnum]
type BaseChart = Chart[BaseNote]

C = TypeVar("C", bound=BaseChart, covariant=True)
T = TypeVar("T", bound=StrEnum, covariant=True)
N = TypeVar("N", bound=BaseNote, covariant=True)


@dataclass
@total_ordering
class Note(Generic[C, T]):
    """Represents a note on a chart.

    - `chart: Chart`: the chart this Note belongs to
    - `time: float`: (in seconds, 0 is the beginning of the song)
    - `lane: int`: The key the user will have to hit to trigger this note
    (which usually corrosponds with it's X position on the highway)
    - `length: float`: the length of the note in seconds, 0 by default
    - `type: str`: the note's type, 'normal' be default

    - `hit: bool`: has this note been hit?
    - `missed: bool`: has this note been missed?
    - `hit_time: float`: when was this note hit?

    - `extra_data: tuple`: ¯\\_(ツ)_//¯"""
    def __init__(self, chart: C, time: Seconds, lane: int, length: Seconds, type: T):
        self.chart = chart
        self.time = time
        self.lane = lane
        self.length = length
        self.type = type

        self.parent: Self | None = None
        self.hit: bool = False
        self.missed: bool = False
        self.hit_time: Seconds | None = None
        self.extra_data: tuple[Any, ...] | None = None

    @property
    def end(self) -> Seconds:
        return self.time + self.length

    @end.setter
    def end(self, v: Seconds) -> None:
        self.length = v - self.time

    @property
    def is_sustain(self) -> bool:
        return self.length > 0

    def __lt__(self, other: Event | Note[C, T]) -> bool:
        if isinstance(other, Note):
            return (self.time, self.lane, self.type) < (other.time, other.lane, other.type)
        elif isinstance(other, Event):
            return self.time < other.time
        raise ValueError

    def __repr__(self) -> str:
        end = f"-{self.end:.3f}"
        return f"<{self.__class__.__name__} L{self.lane}|T'{self.type}'@{self.time:.3f}{end if self.length else ''}>"

    def __str__(self) -> str:
        return self.__repr__()


@dataclass
@total_ordering
class Event:
    """A very basic event that happens at a time.

    * `time: float`: event start in seconds."""
    time: Seconds

    def __lt__(self, other: Event) -> bool:
        return self.time < other.time

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}@{self.time:.3f}>"

    def __str__(self) -> str:
        return self.__repr__()


@dataclass
class BPMChangeEvent(Event):
    """Event indicating the song's BPM has changed.

    * `new_bpm: float`: the new BPM going forward.
    * `time: float`: event start in seconds."""
    new_bpm: float

    @property
    def beat_length(self) -> Seconds:
        return 1 / (self.new_bpm / 60)

    @beat_length.setter
    def beat_length(self, v: Seconds) -> None:
        self.new_bpm = (1 / v) * 60

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}@{self.time:.3f} bpm:{self.new_bpm}>"

    def __str__(self) -> str:
        return self.__repr__()


@dataclass
class CountdownEvent(Event):
    """Event indicating a pause in the chart.

    * `length: float`: the length of this countdown.
    * `time: float`: event start in seconds."""
    length: float

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}@{self.time:.3f} length:{self.length}>"

    def __str__(self) -> str:
        return self.__repr__()


class Chart(Generic[N]):
    """A collection of notes and events, with helpful metadata."""
    def __init__(self, metadata: ChartMetadata, notes: Sequence[N], events: Sequence[Event]) -> None:
        self.metadata: ChartMetadata = metadata
        self.notes = list(notes)
        self.events = list(events)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.metadata.gamemode}/{self.metadata.instrument}/{self.metadata.difficulty}>"

    def __str__(self) -> str:
        return self.__repr__()

    def events_by_type[T: Event](self, t: type[T]) -> list[T]:
        return [e for e in self.events if isinstance(e, t)]

    def calculate_indices(self) -> None:
        """An overridable method for charts to generate their NIndex collections"""
        pass
