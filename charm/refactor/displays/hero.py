
from arcade import get_window

from charm.lib.types import Seconds
from charm.lib.displayables import HPBar, Timer
from charm.refactor.charts.hero import HeroChart
from charm.refactor.engines.hero import HeroEngine
from charm.refactor.highways.hero import HeroHighway
from charm.refactor.generic.display import Display


class HeroDisplay(Display[HeroEngine, HeroChart]):

    def __init__(self, engine: HeroEngine, charts: tuple[HeroChart, ...]):
        super().__init__(engine, charts)
        self._win: "DigiWindow" = get_window()  # type: ignore | aaa shut up Arcade
        self.chart = charts[0]

        self.highway: HeroHighway = HeroHighway(self.chart, engine, (0, 0), (self._win.width // 4, self._win.height))
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
