from __future__ import annotations

from dataclasses import dataclass
from functools import cache, total_ordering
from pathlib import Path
from typing import Any, Self

from charm.lib.types import Seconds
from charm.objects.lyric_animator import LyricEvent


class Metadata:
    """For menu sorting/display."""
    def __init__(
        self,
        *,
        path: Path,
        title: str,
        artist: str | None = None,
        album: str | None = None,
        length: Seconds | None = None,
        genre: str | None = None,
        year: int | None = None,
        difficulty: int | None = None,
        charter: str | None = None,
        preview_start: Seconds | None = None,
        preview_end: Seconds | None = None,
        source: str | None = None,
        hash: str | None = None,
        gamemode: str | None = None
    ):
        self.title = title
        self.artist = artist
        self.album = album
        self.length = length
        self.genre = genre
        self.year = year
        self.difficulty = difficulty
        self.charter = charter
        self.preview_start = preview_start
        self.preview_end = preview_end
        self.source = source
        self.hash = hash
        self.path = path
        self.gamemode = gamemode

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.hash} ({self.title}:{self.artist}:{self.album})>"

    def __str__(self) -> str:
        return self.__repr__()


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

    - `extra_data: tuple`: ¯\_(ツ)_/¯"""  # noqa
    chart: Chart
    time: Seconds
    lane: int
    length: Seconds = 0
    type: str = "normal"
    value: int = 0

    hit: bool = False
    missed: bool = False
    hit_time: Seconds | None = None

    extra_data: tuple[Any, ...] | None = None

    @property
    def end(self) -> Seconds:
        return self.time + self.length

    @end.setter
    def end(self, v: Seconds):
        self.length = v - self.time

    @property
    def icon(self) -> str:
        return NotImplemented

    @property
    def is_sustain(self) -> bool:
        return self.length > 0

    def __lt__(self, other) -> bool:
        if isinstance(other, Note):
            return (self.time, self.lane) < (other.time, other.lane)
        elif isinstance(other, Event):
            if self.time == other.time:
                return False
            return self.time < other.time

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

    def __lt__(self, other) -> bool:
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
    def beat_length(self, v: Seconds):
        self.new_bpm = (1 / v) * 60

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}@{self.time:.3f} bpm:{self.new_bpm}>"

    def __str__(self) -> str:
        return self.__repr__()


class Chart:
    """A collection of notes and events, with helpful metadata."""
    def __init__(self, song: Song[Self], gamemode: str, difficulty: str, instrument: str, lanes: int, hash: str | None) -> None:
        self.song = song
        self.gamemode = gamemode
        self.difficulty = difficulty
        self.instrument = instrument
        self.lanes = lanes
        self.hash = hash

        self.notes: list[Note] = []
        self.events: list[Event] = []
        self.bpm: float = None


class Song[C: Chart]:
    """A list of charts and global events, with some helpful metadata."""
    def __init__(self, path: Path):
        self.path: Path = path
        self.metadata = Metadata(path=path, title=path.stem)
        self.charts: list[C] = []
        self.events: list[Event] = []
        self.lyrics: list[LyricEvent] = []

    @cache
    def get_chart(self, difficulty: str | None = None, instrument: str | None = None) -> C | None:
        if difficulty is None and instrument is None:
            raise ValueError(".get_chart() called with no arguments!")
        charts = (c for c in self.charts if
            (difficulty is None or difficulty == c.difficulty)
            and (instrument is None or instrument == c.instrument))
        return next(charts, None)

    def events_by_type[T: Event](self, t: type[T]) -> list[T]:
        return [e for e in self.events if isinstance(e, t)]

    @classmethod
    def parse(cls, path: Path) -> Self:
        raise NotImplementedError
