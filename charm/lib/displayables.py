from __future__ import annotations

from typing import TYPE_CHECKING, Protocol
from arcade import LBWH, Sprite, SpriteCircle, Text, LRBT, XYWH, color as colors, \
    draw_rect_filled, draw_rect_outline, draw_sprite, get_window
import arcade
from arcade.types import Color
from arcade.color import BLACK

from charm.lib.anim import ease_circout, lerp, ease_linear, LerpData, perc
from charm.lib.charm import CharmColors
from charm.lib.utils import map_range, px_to_pt

from charm.core.generic import BaseEngine

if TYPE_CHECKING:
    from charm.lib.gamemodes.fnf import CameraFocusEvent

class Displayable(Protocol):
    def update(self, song_time: float) -> None:
        ...

    def draw(self) -> None:
        ...

class HPBar:
    def __init__(self, x: float, y: float,
                 height: float, width: float,
                 engine: BaseEngine,
                 color: Color = BLACK,
                 center_sprite: Sprite | None = None):
        self.x = x
        self.y = y
        self.height = height
        self.width = width
        self.color = color
        self.engine = engine
        self.center_sprite: Sprite = center_sprite if center_sprite else SpriteCircle(int(self.height * 2), CharmColors.PURPLE)

        self.center_sprite.center_x = x
        self.center_sprite.center_y = y

    def update(self, song_time: float) -> None:
        pass

    def draw(self) -> None:
        hp_min = self.x - self.width // 2
        hp_max = self.x + self.width // 2
        hp_normalized = map_range(self.engine.hp, self.engine.min_hp, self.engine.max_hp, 0, 1)
        hp = lerp(hp_min, hp_max, hp_normalized)
        draw_rect_filled(LRBT(
            hp_min, hp_max,
            self.y - self.height // 2, self.y + self.height // 2),
            self.color
        )
        self.center_sprite.center_x = hp
        draw_sprite(self.center_sprite)

class Timer:
    def __init__(self, width: int, total_time: float, start_time: float = 0, paused: bool = False,
                 bar_bg_color: Color = colors.WHITE, bar_fill_color: Color = CharmColors.FADED_PURPLE, bar_border_color: Color = colors.BLACK,
                 height: int = 33, text_color: Color = colors.BLACK, text_font: str = "bananaslip plus",
                 x: float = 0, y: float = 0):
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
        return max(0.0, self.current_time / self.total_time)

    @property
    def fill_px(self) -> int:
        return int(self.width * self.percentage)

    @property
    def current_seconds(self) -> float:
        return max(0.0, self.current_time + self.current_time_offset) % 60

    @property
    def current_minutes(self) -> int:
        return int(max(0.0, self.current_time + self.current_time_offset) // 60)

    @property
    def total_seconds(self) -> float:
        return (self.total_time + self.total_time_offset) % 60

    @property
    def total_minutes(self) -> int:
        return int((self.total_time + self.total_time_offset) // 60)

    @property
    def display_string(self) -> str:
        return f"{int(self.current_minutes)}:{int(self.current_seconds):02} / {int(self.total_minutes)}:{int(self.total_seconds):02}"

    @property
    def center_x(self) -> float:
        return self.x + (self.width / 2)

    @property
    def center_y(self) -> float:
        return self.y + (self.height / 2)

    @center_x.setter
    def center_x(self, v: float) -> None:
        self.x = v - (self.width / 2)
        self._label.x = v

    @center_y.setter
    def center_y(self, v: float) -> None:
        self.y = v - (self.height / 2)
        self._label.y = v + 5

    def lerp_current_time(self, offset: float, duration: float,
                          start_time: float = None) -> None:
        start_position = self.current_time_offset
        start_time = start_time or self._clock
        self._current_time_lerps.append(
            LerpData(start_position, offset, start_time, start_time + duration)
        )

    def lerp_total_time(self, offset: float, duration: float,
                        start_time: float = None) -> None:
        start_position = self.total_time_offset
        start_time = start_time or self._clock
        self._total_time_lerps.append(
            LerpData(start_position, offset, start_time, start_time + duration)
        )

    def update(self, delta_time: float, auto_update_time: bool = False) -> None:
        if not self.paused:
            self._clock += delta_time
            if auto_update_time:
                self.current_time += delta_time
        self._label.text = self.display_string

        for l in [v for v in self._current_time_lerps if v.end_time > self._clock]:
            self.current_time_offset = ease_linear(l.minimum, l.maximum, perc(l.start_time, l.end_time, self._clock))

        for l in [v for v in self._total_time_lerps if v.end_time > self._clock]:
            self.total_time_offset = ease_linear(l.minimum, l.maximum, perc(l.start_time, l.end_time, self._clock))

    def draw(self) -> None:
        draw_rect_filled(XYWH(self.center_x, self.center_y, self.width, self.height), self.bar_bg_color)
        draw_rect_filled(LRBT(self.x, self.x + self.fill_px, self.y, self.y + self.height), self.bar_fill_color)
        draw_rect_outline(XYWH(self.center_x, self.center_y, self.width, self.height), self.bar_border_color, 1)
        self._label.draw()

class Spotlight:
    def __init__(self, camera_events: list[CameraFocusEvent]) -> None:
        self.camera_events = camera_events
        self.window = get_window()

        self.last_camera_event: CameraFocusEvent | None = None
        self.last_spotlight_change = 0

        self.last_spotlight_position_left = 0
        self.last_spotlight_position_right = self.window.width

        self.go_to_spotlight_position_left = 0
        self.go_to_spotlight_position_right = self.window.width

        self.spotlight_position_left = 0
        self.spotlight_position_right = self.window.width

    def update(self, song_time: float) -> None:
        focus_pos = {
            1: (0, self.window.center_x),
            0: (self.window.center_x, self.window.width),
            2: (0, self.window.width)
        }
        cameraevents = [e for e in self.camera_events if e.time < song_time + 0.25]
        if cameraevents:
            current_camera_event = cameraevents[-1]
            if self.last_camera_event != current_camera_event:
                self.last_spotlight_change = song_time
                self.last_spotlight_position_left, self.last_spotlight_position_right = self.spotlight_position_left, self.spotlight_position_right
                self.go_to_spotlight_position_left, self.go_to_spotlight_position_right = focus_pos[current_camera_event.focused_player]
                self.last_camera_event = current_camera_event

        self.spotlight_position_left = ease_circout(self.last_spotlight_position_left, self.go_to_spotlight_position_left, perc(self.last_spotlight_change, self.last_spotlight_change + 0.125, song_time))
        self.spotlight_position_right = ease_circout(self.last_spotlight_position_right, self.go_to_spotlight_position_right, perc(self.last_spotlight_change, self.last_spotlight_change + 0.125, song_time))

    def draw(self) -> None:
        # LEFT
        draw_rect_filled(LRBT(
            self.spotlight_position_left - self.window.center_x, self.spotlight_position_left, 0, self.window.height),
            colors.BLACK[:3] + (127,)
        )

        # RIGHT
        draw_rect_filled(LRBT(
            self.spotlight_position_right, self.spotlight_position_right + self.window.center_x, 0, self.window.height),
            colors.BLACK[:3] + (127,)
        )

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
