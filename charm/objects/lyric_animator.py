from copy import copy
from dataclasses import dataclass, field

import arcade
import pyglet

Seconds = float

@dataclass
class LyricEvent:
    time: Seconds
    length: Seconds
    text: str
    karaoke: str = ""

    _labels: list[arcade.Text] = field(default_factory=list)
    _batch: pyglet.graphics.Batch = field(default_factory=pyglet.graphics.Batch)

    @property
    def end_time(self) -> Seconds:
        return self.time + self.length

    @end_time.setter
    def end_time(self, v: Seconds):
        self.length = v - self.time

    def get_labels(self, x: float, y: float) -> arcade.Text:
        if not self._labels:
            label_shadow = arcade.Text(self.text, x + 2, y - 2, font_name = "bananaslip plus", font_size = 24, color = (0, 0, 0, 127), align = "center", anchor_x = "center", batch = self._batch)
            label_under = arcade.Text(self.text, x, y, font_name = "bananaslip plus", font_size = 24, color = (0, 0, 0, 255), align = "center", anchor_x = "center", batch = self._batch)
            self._labels.append(label_shadow)
            self._labels.append(label_under)
            if self.karaoke:
                label_over = arcade.Text(self.karaoke, label_under.left, y, font_name = "bananaslip plus", font_size = 24, color = (255, 255, 0, 255), align = "left", anchor_x = "left", batch = self._batch)
                self._labels.append(label_over)
        return self._labels

    def draw(self):
        self._batch.draw()

class LyricAnimator:
    def __init__(self, x: float, y: float, events: list[LyricEvent] = None) -> None:
        self.x = x
        self.y = y

        self.events: list[LyricEvent] = [] if events is None else events
        self.active_subtitles = [copy(e) for e in self.events]
        self.current_subtitles: list[LyricEvent] = []

        self.song_time = 0

        self.show_box = True

    def update(self, song_time: Seconds):
        self.song_time = song_time
        for subtitle in self.current_subtitles:
            if subtitle.end_time < self.song_time:
                self.current_subtitles.remove(subtitle)
        for subtitle in self.active_subtitles:
            if subtitle.time <= self.song_time:
                self.current_subtitles.append(subtitle)
                self.active_subtitles.remove(subtitle)

    def draw(self):
        if self.current_subtitles:
            self.current_subtitles[-1].get_labels(self.x, self.y)
            self.current_subtitles[-1].draw()
