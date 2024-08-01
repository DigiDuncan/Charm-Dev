from __future__ import annotations

from dataclasses import dataclass
from functools import total_ordering
from typing import Any

from charm.lib.types import Seconds

@dataclass
@total_ordering
class Note:
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
    type: str = "normal"

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
            return (self.time, self.lane) < (other.time, other.lane)
        elif isinstance(other, Event):
            if self.time == other.time:
                return False
            return self.time < other.time
        else:
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


# ?: I removed the reference to the Chart's parent Song here, because during the parsing phase we don't
# necessarily know what song we're attaching ourselves to.
# Should we attached the Song later in a finalization step?

class Chart[NT: Note]:
    """A collection of notes and events, with helpful metadata."""
    def __init__(self, gamemode: str, difficulty: str, instrument: str, lanes: int, hash: str | None) -> None:
        self.gamemode = gamemode
        self.difficulty = difficulty
        self.instrument = instrument
        self.lanes = lanes
        self.hash = hash

        self.notes: list[NT] = []
        self.events: list[Event] = []
        self.bpm: float = 0.0

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.gamemode}/{self.instrument}/{self.difficulty}>"

    def __str__(self) -> str:
        return self.__repr__()
