from __future__ import annotations

from arcade.types import Point

from charm.refactor.generic import Engine, Chart, NoteSprite
from charm.lib.types import Seconds


class Display[ET: Engine, CT: Chart]:

    def __init__(self, engine: ET, charts: tuple[CT, ...]):
        self.engine: ET = engine
        self.charts: tuple[CT, ...] = charts

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
