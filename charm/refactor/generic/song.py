from functools import cache
from pathlib import Path

from charm.objects.lyric_animator import LyricEvent
from charm.refactor.generic.chart import Chart
from charm.refactor.generic.metadata import Metadata


class Song:
    """A list of charts, with some helpful metadata."""
    def __init__(self, path: Path):
        self.path: Path = path
        self.metadata = Metadata(path=path, title=path.stem)
        self.charts: list[Chart] = []
        self.lyrics: list[LyricEvent] = [] # ?: Lyrics get special treatment right now; should this move?

    @cache
    def get_chart(self, difficulty: str | None = None, instrument: str | None = None) -> Chart | None:
        if difficulty is None and instrument is None:
            raise ValueError(".get_chart() called with no arguments!")
        charts = (c for c in self.charts if
            (difficulty is None or difficulty == c.difficulty)
            and (instrument is None or instrument == c.instrument))
        return next(charts, None)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.path}>"

    def __str__(self) -> str:
        return self.__repr__()
