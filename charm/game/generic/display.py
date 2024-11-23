from __future__ import annotations
from collections.abc import Sequence
from typing import Generic, TypeVar

from arcade.types import Point

from charm.lib.types import Seconds

from .chart import BaseChart
from .engine import BaseEngine
from .sprite import NoteSprite


type BaseDisplay = Display[BaseChart, BaseEngine]

C = TypeVar("C", bound=BaseChart, covariant=True)
E = TypeVar("E", bound=BaseEngine, covariant=True)


class Display(Generic[C, E]):
    def __init__(self, engine: E, charts: Sequence[C]):
        self.engine = engine
        self.charts = charts

    def update(self, song_time: Seconds) -> None:
        pass

    def draw(self) -> None:
        pass

    def pause(self) -> None:
        pass

    def unpause(self) -> None:
        pass

    # -- DEBUG METHODS --

    def debug_fetch_note_sprites_at_point(self, point: Point) -> list[NoteSprite]:
        ...
