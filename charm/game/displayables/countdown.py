from __future__ import annotations

from arcade import LBWH,Text
import arcade
from arcade.types import Color

from charm.lib.anim import ease_linear, perc
from charm.lib.utils import map_range


class Countdown:
    def __init__(self,
                 x: float, y: float, width: float, height: float = 25.0,
                 color: Color = arcade.color.WHITE,
                 units_per_second: float = 1.0) -> None:
        self.units_per_second = units_per_second

        self.x = x - (width / 2)
        self.y = y
        self.width = width
        self.height = height

        self.color = color

        self.text = Text("", self.x + self.width / 2.0, self.y + self.height + 10,
                         arcade.color.BLACK, 48,
                         int(self.width),
                         font_name = "bananaslip plus",
                         anchor_x = "center")

        self.start_time: float = None
        self.duration: float = None
        self.current_time = 0.0

    def use(self, start_time: float, duration: float) -> None:
        self.start_time = start_time
        self.duration = duration

    @property
    def time_remaining(self) -> float:
        if self.start_time is None:
            return 0.0
        return self.duration - (self.current_time - self.start_time)

    def update(self, song_time: float) -> None:
        self.current_time = song_time
        self.text.text = f"{int(self.time_remaining)}" if self.time_remaining > 1 else "Ready!"
        if self.time_remaining < 0.0:
            self.start_time = None
            self.duration = None

    def draw(self) -> None:
        if self.start_time is None:
            return
        progress = map_range(self.current_time, self.start_time,
                             self.start_time + self.duration,
                             self.width, 0)
        rect = LBWH(self.x, self.y, progress, self.height)

        if self.time_remaining > 1:
            arcade.draw_rect_filled(rect, self.color)
            self.text.draw()
        elif self.time_remaining > 0:
            alpha = int(ease_linear(255, 0, perc(1, 0, self.time_remaining)))
            arcade.draw_rect_filled(rect, self.color.replace(a = alpha))
            self.text.color = self.text.color.replace(a = alpha)
            self.text.draw()
