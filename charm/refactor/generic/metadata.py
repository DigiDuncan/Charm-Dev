from __future__ import annotations

from dataclasses import dataclass
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


@dataclass
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
    hash: str | None = None
    gamemode: str | None = None

    @property
    def shortcode(self) -> str:
        return f"{self.title}:{self.artist}:{self.album}"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.hash} ({self.shortcode})>"

    def __str__(self) -> str:
        return self.__repr__()

    def update(self, other: ChartSetMetadata) -> ChartSetMetadata:
        #! Hard codded so much lorde
        return ChartSetMetadata(
            other.path if other.path is not None else self.path,
            other.title if other.title is not None else self.title,
            other.artist if other.artist is not None else self.artist,
            other.album if other.album is not None else self.album,
            other.length if other.length is not None else self.length,
            other.genre if other.genre is not None else self.genre,
            other.year if other.year is not None else self.year,
            other.difficulty if other.difficulty is not None else self.difficulty,
            other.charter if other.charter is not None else self.charter,
            other.preview_start if other.preview_start is not None else self.preview_start,
            other.preview_end if other.preview_end is not None else self.preview_end,
            other.source if other.source is not None else self.source,
            other.hash if other.hash is not None else self.hash,
            other.gamemode if other.gamemode is not None else self.gamemode
        )
