from __future__ import annotations

from dataclasses import dataclass
import dataclasses
from pathlib import Path

from charm.lib.types import Seconds

# ?: I removed the reference to the Chart's parent ChartSet here, because during the parsing
# phase we don't necessarily know what ChartSet we're attaching ourselves to.
# Should we attached the ChartSet later in a finalization step?

class ChartMetadata:
    """Chart metadata needed to later parse the chart fully"""
    def __init__(self, gamemode: str, difficulty: str, path: Path, instrument: str | None = None) -> None:
        self.gamemode = gamemode
        self.difficulty = difficulty
        self.instrument = instrument
        self.path = path

    def __hash__(self) -> int:
        return hash((self.gamemode, self.difficulty, self.instrument, str(self.path)))

    def __eq__(self, other: ChartMetadata) -> bool:
        return (self.path, self.gamemode, self.difficulty, self.instrument) == (other.path, other.gamemode, other.difficulty, other.instrument)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.gamemode}/{self.instrument}/{self.difficulty}>"

    def __str__(self) -> str:
        return self.__repr__()


@dataclass(eq=True)
class ChartSetMetadata:
    """For menu sorting/display."""
    path: Path
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    length: Seconds | None = None
    genre: str | None = None
    year: int | None = None
    difficulty: int | None = None  # NOTE: This isn't the same as per-chart difficulty, and is more like a generic rating. Change?
    charter: str | None = None
    preview_start: Seconds | None = None
    preview_end: Seconds | None = None
    source: str | None = None
    album_art: str | None = None
    hash: str | None = None  # ! Unused will hopefully become the cross device hash
    gamemode: str | None = None

    @property
    def shortcode(self) -> str:
        return f"{self.title}:{self.artist}:{self.album}"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.hash} ({self.shortcode})>"

    def __str__(self) -> str:
        return self.__repr__()

    def __hash__(self) -> int:
        return hash(str(self.path))

    def update(self, other: ChartSetMetadata) -> ChartSetMetadata:
        k = {}
        for field in dataclasses.fields(self):
            o = getattr(other, field.name)
            k[field.name] = o if o is not None else getattr(self, field.name)
        return ChartSetMetadata(**k)
