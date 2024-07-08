from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from charm.lib.digiwindow import DigiWindow
    from charm.lib.generic.engine import Engine
    from charm.lib.generic.song import Chart
    from charm.lib.types import Seconds


class Display[T: Engine, CT: Chart]:

    def __init__(self, window: DigiWindow, engine: T, charts: tuple[CT, ...]):
        self._win: DigiWindow = window
        self._engine: T = engine
        self._charts: tuple[CT, ...] = charts

    def update(self, song_time: Seconds) -> None:
        pass

    def draw(self) -> None:
        pass

    def pause(self) -> None:
        pass

    def unpause(self) -> None:
        pass
