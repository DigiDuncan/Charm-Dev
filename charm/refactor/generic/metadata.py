from dataclasses import dataclass
from pathlib import Path

from charm.lib.types import Seconds


@dataclass
class Metadata:
    """For menu sorting/display."""
    path: Path
    title: str
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
