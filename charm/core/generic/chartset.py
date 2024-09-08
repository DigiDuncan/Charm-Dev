from pathlib import Path

from .metadata import ChartSetMetadata, ChartMetadata


class ChartSet:
    """A list of charts, with some helpful metadata."""
    def __init__(self, path: Path, metadata: ChartSetMetadata, charts: list[ChartMetadata] | None = None):
        self.path: Path = path
        self.metadata: ChartSetMetadata = metadata
        self.charts: list[ChartMetadata] = charts or []

    @property
    def gamemodes(self) -> set[str]:
        return set(chart.gamemode for chart in self.charts)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.path}>"

    def __str__(self) -> str:
        return self.__repr__()
