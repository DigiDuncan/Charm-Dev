from abc import ABC, abstractmethod
from pathlib import Path
from charm.refactor.generic.chartset import AbstractChartSet


class AbstractParser(ABC):
    @abstractmethod
    def __init__(self) -> None:
        ...

    @classmethod
    @abstractmethod
    def parse_chartset(cls, path: Path) -> AbstractChartSet:
        ...


class Parser(AbstractParser):
    ...
