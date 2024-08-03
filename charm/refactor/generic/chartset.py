from functools import cache
from pathlib import Path

from charm.objects.lyric_animator import LyricEvent
from charm.refactor.generic.chart import Chart
from charm.refactor.generic.metadata import Metadata


class ChartSet:
    """A list of charts, with some helpful metadata."""
    def __init__(self, path: Path):
        self.path: Path = path
        self.metadata = Metadata(path=path, title=path.stem)
        self.charts: list[Chart] = []
        self.lyrics: list[LyricEvent] = [] # ?: Lyrics get special treatment right now; should this move?

    @cache
    def get_chart(self, *args, **kwargs) -> Chart | None:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.path}>"

    def __str__(self) -> str:
        return self.__repr__()
