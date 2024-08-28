from pathlib import Path

from charm.refactor.generic.metadata import ChartSetMetadata, ChartMetadata


class ChartSet:
    """A list of charts, with some helpful metadata."""
    def __init__(self, path: Path, metadata: ChartSetMetadata, charts: list[ChartMetadata] = None):
        self.path: Path = path
        self.metadata: ChartSetMetadata = metadata
        self.charts: list[ChartMetadata] = charts or []

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.path}>"

    def __str__(self) -> str:
        return self.__repr__()
