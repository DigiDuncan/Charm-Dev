
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from charm.lib.digiview import DigiWindow
from collections.abc import Sequence

from arcade import get_window

from charm.lib.types import Seconds
from charm.lib.displayables import Timer

from charm.core.generic import Display
from .chart import FiveFretChart
from .engine import FiveFretEngine
from .highway import FiveFretHighway


class FiveFretDisplay(Display[FiveFretChart, FiveFretEngine]):
    def __init__(self, engine: FiveFretEngine, charts: Sequence[FiveFretChart]):
        super().__init__(engine, charts)
        self._win: DigiWindow = get_window()  # type: ignore | aaa shut up Arcade
        self.chart = charts[0]

        self.highway: FiveFretHighway = FiveFretHighway(self.chart, engine, (0, 0), (self._win.width // 4, self._win.height))
        self.highway.x = self._win.center_x - self.highway.w // 2

        # Timer
        self.timer = Timer(250, 60)
        self.timer.center_x = self._win.center_x
        self.timer.center_y = self._win.height - 60

    def update(self, song_time: Seconds) -> None:
        self._song_time = song_time

        self.highway.update(song_time)

        self.timer.current_time = song_time
        self.timer.update(self._win.delta_time)

    def draw(self) -> None:
        self.highway.draw()

        # self.hp_bar.draw()
        self.timer.draw()
