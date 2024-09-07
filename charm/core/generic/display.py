from __future__ import annotations
from collections.abc import Sequence

from arcade.types import Point

from charm.lib.types import Seconds

from .engine import Engine
from .chart import Chart
from .sprite import NoteSprite


class Display:
    def __init__(self, engine: Engine, charts: Sequence[Chart]):
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
