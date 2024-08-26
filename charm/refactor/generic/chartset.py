from pathlib import Path

from charm.refactor.generic.chart import ChartMetadata
from charm.refactor.generic.metadata import Metadata


class ChartSet:
    """A list of charts, with some helpful metadata."""
    def __init__(self, path: Path, charts: list[ChartMetadata] = None):
        self.path: Path = path
        self.metadata = Metadata(path=path, title=path.stem)
        self.charts: list[ChartMetadata] = charts or []

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.path}>"

    def __str__(self) -> str:
        return self.__repr__()
