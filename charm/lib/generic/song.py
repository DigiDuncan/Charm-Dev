from __future__ import annotations

from dataclasses import dataclass
import dataclasses
from functools import cache, total_ordering
from pathlib import Path
from typing import Optional


Seconds = float
Milliseconds = float

@dataclass
class Metadata:
    """For menu sorting/display."""
    title: str
    artist: str = None
    album: str = None
    length: Seconds = None
    genre: str = None
    year: int = None
    difficulty: int = None
    charter: str = None
    preview_start: Seconds = None
    preview_end: Seconds = None
    mod: str = None
    hash: str = None
    path: Path = None
    gamemode: str = None

    def get(self, key, default = None):
        """Basically a duplicate of dict.get()"""
        fields = [f.name for f in dataclasses.fields(self)]
        if key not in fields:
            return default
        val = getattr(self, key)
        if val is None:
            return default
        else:
            return val


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

    hit: bool = False
    missed: bool = False
    hit_time: Optional[Seconds] = None

    extra_data: tuple = None

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


@dataclass
@total_ordering
class Event:
    """A very basic event that happens at a time.

    * `time: float`: event start in seconds."""
    time: Seconds

    def __lt__(self, other) -> bool:
        return self.time < other.time


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


class Chart:
    """A collection of notes and events, with helpful metadata."""
    def __init__(self, song: 'Song', gamemode: str, difficulty: str, instrument: str, lanes: int, hash: str) -> None:
        self.song: Song = song
        self.gamemode = gamemode
        self.difficulty = difficulty
        self.instrument = instrument
        self.lanes = lanes
        self.hash = hash

        self.notes: list[Note] = []
        self.events: list[Event] = []
        self.bpm: float = None


class Song:
    """A list of charts and global events, with some helpful metadata."""
    def __init__(self, path: Path):
        self.path: Path = path
        self.metadata = Metadata(path.stem, "Unknown Artist", "Unknown Album")
        self.charts: list[Chart] = []
        self.events: list[Event] = []

    @cache
    def get_chart(self, difficulty = None, instrument = None):
        if difficulty is None and instrument is None:
            raise ValueError(".get_chart() called with no arguments!")
        elif difficulty is not None and instrument is not None:
            return next((c for c in self.charts if c.difficulty == difficulty and c.instrument == instrument), None)
        elif difficulty is not None:
            return next((c for c in self.charts if c.difficulty == difficulty), None)
        elif instrument is not None:
            return next((c for c in self.charts if c.instrument == instrument), None)

    def events_by_type(self, t: type):
        return [e for e in self.events if isinstance(e, t)]

    @classmethod
    def parse(cls, folder: Path):
        raise NotImplementedError
