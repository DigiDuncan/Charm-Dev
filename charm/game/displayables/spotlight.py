from __future__ import annotations

from typing import TYPE_CHECKING
from arcade import (LRBT, color as colors, draw_rect_filled, get_window)

from charm.lib.anim import ease_circout, perc


if TYPE_CHECKING:
    from charm.lib.gamemodes.fnf import CameraFocusEvent


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