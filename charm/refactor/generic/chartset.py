from abc import ABC, abstractmethod
from collections.abc import Sequence
from functools import cache
from pathlib import Path

from charm.objects.lyric_animator import LyricEvent
from charm.refactor.generic.chart import AbstractChart, Chart
from charm.refactor.generic.metadata import Metadata

class AbstractChartSet(ABC):
    @abstractmethod
    def __init__(self, path: Path, charts: list[AbstractChart]):
        ...

class ChartSet(AbstractChartSet):
    """A list of charts, with some helpful metadata."""
    def __init__(self, path: Path, charts: Sequence[AbstractChart] | None = None):
        self.path: Path = path
        self.metadata = Metadata(path=path, title=path.stem)
        self.charts: list[AbstractChart] = charts or []
        self.lyrics: list[LyricEvent] = [] # ?: Lyrics get special treatment right now; should this move?

    @cache
    def get_chart(self) -> Chart | None:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.path}>"

    def __str__(self) -> str:
        return self.__repr__()
