
from __future__ import annotations
import random
from typing import TYPE_CHECKING

import arcade

from charm.game.displayables.lyric_animator import LyricAnimator, LyricEvent
if TYPE_CHECKING:
    from charm.core.digiview import DigiWindow
from collections.abc import Sequence

from arcade import Text, get_window

from charm.lib.types import Seconds
from charm.game.displayables import NoteStreakDisplay, NumericDisplay, Timer

from charm.game.generic import Display
from .chart import FiveFretChart, SectionEvent
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
        self.timer.center_x = self._win.width - 135
        self.timer.center_y = 60

        # Lyric animator
        if lyrics := self.chart.events_by_type(LyricEvent):
            self.lyric_animator: LyricAnimator = LyricAnimator(self._win.width / 2, self._win.height * 0.9, lyrics)
            self.lyric_animator.prerender()
        else:
            self.lyric_animator: LyricAnimator = None

        self.sections = self.chart.events_by_type(SectionEvent)
        self.current_section = self.sections[0] if self.sections else "No Section"

        # Score display
        self.score_display = NumericDisplay(self._win.width - 10, 200, 64, color = arcade.color.BLACK, show_zeroes = False)
        self.combo_display = Text("| 0", self._win.center_x, 5, arcade.color.BLACK, 20, anchor_x = "left", anchor_y = "bottom", align = "left", font_name = "bananaslip plus")
        self.multipler_display = Text("1x ", self._win.center_x, 5, arcade.color.BLACK, 20, anchor_x = "right", anchor_y = "bottom", align = "right", font_name = "bananaslip plus")
        self.multipler_shadow_display = Text("1x ", self._win.center_x + 2, 3, arcade.color.BLACK.replace(a = 127), 20, anchor_x = "right", anchor_y = "bottom", align = "right", font_name = "bananaslip plus")
        self.section_display = Text("No Section", self.timer.x + self.timer.width, self.timer.y + self.timer.height + 5, arcade.color.BLACK, 24, align = "right", font_name = "bananaslip plus", anchor_x = "right", anchor_y = "bottom")

        # Note streak popup
        self.note_streak_display = NoteStreakDisplay(self.engine, self._win.center_x, self._win.height - 100)

    def update(self, song_time: Seconds) -> None:
        self._song_time = song_time

        self.highway.update(song_time)

        self.timer.current_time = song_time
        self.timer.update(self._win.delta_time)

        if self.lyric_animator:
            self.lyric_animator.update(song_time)

        if self.sections:
            sec = self.current_section = self.chart.indices.section_time.lteq(song_time)
            self.current_section = sec.name if sec else "No Section"

        self.score_display.score = self.engine.score
        self.combo_display.text = f"| {self.engine.streak}"
        self.section_display.text = self.current_section
        self.multipler_display.text = f"{self.engine.multiplier}x "
        self.multipler_shadow_display.text = f"{self.engine.multiplier}x "
        match self.engine.multiplier:
            case 1:
                self.multipler_display.color = arcade.color.FOREST_GREEN
            case 2:
                self.multipler_display.color = arcade.color.DARK_ORANGE
            case 3:
                self.multipler_display.color = arcade.color.DARK_RED
            case 4:
                self.multipler_display.color = arcade.color.PURPLE_HEART
            case _:
                self.multipler_display.color = arcade.color.DARK_CYAN

        self.note_streak_display.update(self._song_time)

    def draw(self) -> None:
        self.highway.draw()

        # self.hp_bar.draw()
        self.timer.draw()

        if self.lyric_animator:
            self.lyric_animator.draw()

        self.score_display.draw()
        self.combo_display.draw()
        self.section_display.draw()
        self.multipler_shadow_display.draw()
        self.multipler_display.draw()
        self.note_streak_display.draw()
