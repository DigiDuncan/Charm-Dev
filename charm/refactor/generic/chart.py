from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
from functools import total_ordering
from typing import Any

from charm.lib.types import Seconds

from charm.refactor.generic.metadata import ChartMetadata


@dataclass
@total_ordering
class Note[NT: str]:
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
    chart: Chart
    time: Seconds
    lane: int
    length: Seconds = 0
    # A basic string technically might not satisfy a subclass of string (not that we are doing that so its fine)
    type: NT = "normal"  # type: ignore --

    parent: Note[NT] | None = None

    hit: bool = False
    missed: bool = False
    hit_time: Seconds | None = None

    extra_data: tuple[Any, ...] | None = None

    @property
    def end(self) -> Seconds:
        return self.time + self.length

    @end.setter
    def end(self, v: Seconds) -> None:
        self.length = v - self.time

    # !: Removed .icon

    @property
    def is_sustain(self) -> bool:
        return self.length > 0

    def __lt__(self, other: Event | Note) -> bool:
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


class Chart[NT: Note]:
    """A collection of notes and events, with helpful metadata."""
    def __init__(self, metadata: ChartMetadata, notes: list[NT], events: list[Event]) -> None:
        self.metadata: ChartMetadata = metadata
        self.notes: list[NT] = notes
        self.events: list[Event] = events

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.metadata.gamemode}/{self.metadata.instrument}/{self.metadata.difficulty}>"

    def __str__(self) -> str:
        return self.__repr__()

    def events_by_type[T: Event](self, t: type[T]) -> list[T]:
        return [e for e in self.events if isinstance(e, t)]
