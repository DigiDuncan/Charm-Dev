from __future__ import annotations

import statistics

import pyglet
from arcade import color as colors


class FPSCounter:
    def __init__(self):
        self.enabled = False
        self.frames: int = 0
        self.fps_averages: list[float] = []
        self.fps_label = pyglet.text.Label(
            "???.? FPS",
            font_name='bananaslip plus',
            font_size=12,
            anchor_x='left', anchor_y='top',
            color=(0, 0, 0, 0xFF)
        )
        self.fps_shadow_label = pyglet.text.Label(
            "???.? FPS",
            font_name='bananaslip plus',
            font_size=12,
            anchor_x='left', anchor_y='top',
            color=(0xAA, 0xAA, 0xAA, 0xFF)
        )

    def on_update(self, delta_time: float) -> None:
        self.frames += 1
        curr_fps = 1 / delta_time
        # FPS Counter
        if self.frames % 30 == 0:
            average = statistics.mean(self.fps_averages)
            self.fps_label.color = colors.BLACK if average >= 120 else colors.RED
            self.fps_label.text = self.fps_shadow_label.text = f"{average:.1f} FPS"
            self.fps_averages.clear()
        else:
            self.fps_averages.append(curr_fps)

    def on_resize(self, width: int, height: int) -> None:
        self.fps_label.position = (0, height, 0)
        self.fps_shadow_label.position = (1, height - 1, 0)

    def draw(self) -> None:
        if not self.enabled:
            return
        self.fps_shadow_label.draw()
        self.fps_label.draw()
