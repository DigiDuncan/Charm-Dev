from __future__ import annotations
from dataclasses import dataclass

from charm.lib.types import Seconds


@dataclass
class Judgement:
    """A Judgement of a single note, basically how close a player got to being accurate with their hit."""
    name: str
    key: str
    ms: float  # maximum
    score: int
    accuracy_weight: float
    hp_change: float = 0

    @property
    def seconds(self) -> Seconds:
        return self.ms / 1000

    def __lt__(self, other: Judgement):
        return self.ms < other.ms

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name}: {self.ms}ms>"

    def __str__(self) -> str:
        return self.__repr__()
