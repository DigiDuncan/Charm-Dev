from arcade.color import Color, WHITE, BLACK
from arcade.draw_commands import draw_rect_filled, draw_rect_outline, draw_lrbt_rectangle_filled
from arcade.text import Text

from charm.lib.anim import ease_linear, LerpData, perc
from charm.lib.charm import CharmColors
from charm.lib.utils import px_to_pt


class Timer:
    def __init__(self, width: int, total_time: float, start_time: float = 0, paused = False,
                 bar_bg_color: Color = WHITE, bar_fill_color: Color = CharmColors.FADED_PURPLE, bar_border_color: Color = BLACK,
                 height: int = 33, text_color: Color = BLACK, text_font: str = "bananaslip plus",
                 x: int = 0, y: int = 0):
        self.width = width
        self.start_time = start_time
        self.total_time = total_time

        self.current_time = start_time
        self.paused = paused

        self.bar_bg_color = bar_bg_color
        self.bar_fill_color = bar_fill_color
        self.bar_border_color = bar_border_color
        self.height = height
        self.text_color = text_color
        self.text_font = text_font

        self.x = x
        self.y = y

        text_size = px_to_pt(self.height)
        self._label = Text("0:00", self.center_x, self.center_y + 5, self.text_color, text_size,
                           align = "center", font_name = self.text_font, anchor_x = "center", anchor_y = "center")

        self._current_time_lerps: list[LerpData] = []
        self._total_time_lerps: list[LerpData] = []

        self._clock = 0

        self.current_time_offset = 0
        self.total_time_offset = 0

    @property
    def percentage(self) -> float:
        return self.current_time / self.total_time

    @property
    def fill_px(self) -> int:
        return int(self.width * self.percentage)

    @property
    def current_seconds(self) -> float:
        return (self.current_time + self.current_time_offset) % 60

    @property
    def current_minutes(self) -> int:
        return (self.current_time + self.current_time_offset) // 60

    @property
    def total_seconds(self) -> float:
        return (self.total_time + self.total_time_offset) % 60

    @property
    def total_minutes(self) -> int:
        return (self.total_time + self.total_time_offset) // 60

    @property
    def display_string(self) -> str:
        return f"{int(self.current_minutes)}:{int(self.current_seconds):02} / {int(self.total_minutes)}:{int(self.total_seconds):02}"

    @property
    def center_x(self) -> int:
        return self.x + (self.width // 2)

    @property
    def center_y(self) -> int:
        return self.y + (self.height // 2)

    @center_x.setter
    def center_x(self, v: int):
        self.x = v - (self.width // 2)
        self._label.x = v

    @center_y.setter
    def center_y(self, v: int):
        self.y = v - (self.height // 2)
        self._label.y = v + 5

    def lerp_current_time(self, offset: float, duration: float,
                          start_time: float = None):
        start_position = self.current_time_offset
        start_time = start_time or self._clock
        self._current_time_lerps.append(
            LerpData(start_position, offset, start_time, start_time + duration)
        )

    def lerp_total_time(self, offset: float, duration: float,
                        start_time: float = None):
        start_position = self.total_time_offset
        start_time = start_time or self._clock
        self._total_time_lerps.append(
            LerpData(start_position, offset, start_time, start_time + duration)
        )

    def update(self, delta_time: float, auto_update_time = False):
        if not self.paused:
            self._clock += delta_time
            if auto_update_time:
                self.current_time += delta_time
        self._label.text = self.display_string

        for lerp in [v for v in self._current_time_lerps if v.end_time > self._clock]:
            self.current_time_offset = ease_linear(lerp.minimum, lerp.maximum, perc(lerp.start_time, lerp.end_time, self._clock))

        for lerp in [v for v in self._total_time_lerps if v.end_time > self._clock]:
            self.total_time_offset = ease_linear(lerp.minimum, lerp.maximum, perc(lerp.start_time, lerp.end_time, self._clock))

    def draw(self):
        draw_rect_filled(self.center_x, self.center_y, self.width, self.height, self.bar_bg_color)
        draw_lrbt_rectangle_filled(self.x, self.x + self.fill_px, self.y, self.y + self.height, self.bar_fill_color)
        draw_rect_outline(self.center_x, self.center_y, self.width, self.height, self.bar_border_color, 1)
        self._label.draw()
