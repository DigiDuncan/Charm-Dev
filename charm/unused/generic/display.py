from __future__ import annotations

from typing import TYPE_CHECKING

from arcade.types import Point


if TYPE_CHECKING:
    from charm.lib.digiwindow import DigiWindow
    from charm.lib.generic.engine import Engine
    from charm.lib.generic.song import Chart
    from charm.lib.generic.sprite import NoteSprite
    from charm.lib.types import Seconds


class Display[ET: Engine, CT: Chart]:

    def __init__(self, window: DigiWindow, engine: ET, charts: tuple[CT, ...]):
        self._win: DigiWindow = window
        self._engine: ET = engine
        self._charts: tuple[CT, ...] = charts

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
