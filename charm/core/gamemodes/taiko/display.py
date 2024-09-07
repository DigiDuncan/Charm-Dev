
from collections.abc import Sequence

from arcade import get_window

from charm.lib.types import Seconds
from charm.lib.displayables import Timer

from charm.core.generic import Display
from .chart import TaikoChart
from .engine import TaikoEngine
from .highway import TaikoHighway


class TaikoDisplay(Display):
    def __init__(self, engine: TaikoEngine, charts: Sequence[TaikoChart]):
        super().__init__(engine, charts)
        self.engine: TaikoEngine
        self.charts: Sequence[TaikoChart]
        self._win: "DigiWindow" = get_window()  # type: ignore | aaa shut up Arcade
        self.chart = charts[0]

        self.highway: TaikoHighway = TaikoHighway(self.chart, engine, (0, self._win.center_y), (self._win.width, 100))

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
