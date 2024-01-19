from copy import copy
from dataclasses import dataclass, field
from typing import Optional

import arcade

Seconds = float

@dataclass
class LyricEvent:
    time: Seconds
    length: Seconds
    text: str
    karaoke: str = ""

    _labels: list[arcade.Text] = field(default_factory=list)

    @property
    def end_time(self) -> Seconds:
        return self.time + self.length

    def get_labels(self, x: float, y: float) -> arcade.Text:
        if not self._labels:
            label_under = arcade.Text(self.text, x, y, font_name = "bananaslip plus", font_size = 24, color = (0, 0, 0, 255), align = "center", anchor_x = "center")
            self._labels.append(label_under)
            if self.karaoke:
                label_over = arcade.Text(self.text, label_under.left, y, font_name = "bananaslip plus", font_size = 24, color = (255, 255, 0, 255), align = "left", anchor_x = "left")
                self._labels.append(label_over)
        return self._label

class LyricAnimator:
    def __init__(self, x: float, y: float, events: list[LyricEvent] = None) -> None:
        self.x = x
        self.y = y

        self.events: list[LyricEvent] = [] if events is None else events
        self.active_subtitles = [copy(e) for e in self.events]
        self.current_subtitles: list[LyricEvent] = []

        self.song_time = 0

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
            label = self.current_subtitles[0].get_label(self.x, self.y)
            label.draw()
