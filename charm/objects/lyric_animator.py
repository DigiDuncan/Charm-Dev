from copy import copy

import arcade
import pyglet
from pyglet import gl

from charm.lib.types import Seconds
from charm.objects.emojilabel import EmojiLabel


gl.glEnable(gl.GL_DEPTH_TEST)


class LyricEvent:
    def __init__(self, time: Seconds, length: Seconds, text: str, karaoke: str = ""):
        self.time = time
        self.length = length
        self.text = text
        self.karaoke = karaoke

        self._labels: list[arcade.Text] = []
        self._batch = pyglet.graphics.Batch()

    @property
    def end_time(self) -> Seconds:
        return self.time + self.length

    @end_time.setter
    def end_time(self, v: Seconds):
        self.length = v - self.time

    def get_labels(self, x: float, y: float, font_size: int) -> list[EmojiLabel]:
        if not self._labels:
            default_emoji_set = "twemoji-bw" if self.karaoke else "twemoji"
            label_shadow = EmojiLabel(self.text, x = x + 2, y = y - 2, z = 3, font_name = "bananaslip plus", font_size = font_size, color = (0, 0, 0, 127), align = "center", anchor_x = "center", batch = self._batch, emojiset = "twemoji-shadow")
            label_under = EmojiLabel(self.text, x = x, y = y, z = 2, font_name = "bananaslip plus", font_size = font_size, color = (0, 0, 0, 255), align = "center", anchor_x = "center", batch = self._batch, emojiset = default_emoji_set)
            self._labels.append(label_shadow)
            self._labels.append(label_under)
            if self.karaoke:
                label_over = EmojiLabel(self.karaoke, x = label_under.x - (label_under.content_width // 2), y = y, z = 1, font_name = "bananaslip plus", font_size = font_size, color = (255, 255, 0, 255), align = "left", anchor_x = "left", batch = self._batch)
                self._labels.append(label_over)
        return self._labels

    def draw(self):
        if not self._labels:
            self.get_labels()
        self._batch.draw()


class LyricAnimator:
    def __init__(self, x: float, y: float, events: list[LyricEvent] = None, width: int = None) -> None:
        self.x = x
        self.y = y
        self.width = int(arcade.get_window().width * 0.9) if width is None else width
        self.max_font_size = 24

        self.events: list[LyricEvent] = [] if events is None else events
        self.active_subtitles = [copy(e) for e in self.events]
        self.current_subtitles: list[LyricEvent] = []

        self.song_time = 0

        self.show_box = True

        self._string_sizes = {}

    def update(self, song_time: Seconds):
        self.song_time = song_time
        for subtitle in self.current_subtitles:
            if subtitle.end_time < self.song_time:
                self.current_subtitles.remove(subtitle)
        for subtitle in self.active_subtitles:
            if subtitle.time <= self.song_time:
                self.current_subtitles.append(subtitle)
                self.active_subtitles.remove(subtitle)

    def get_font_size(self, s: str) -> int:
        if s in self._string_sizes:
            return self._string_sizes[s]
        font_size = self.max_font_size
        label = EmojiLabel(s, x = 0, y = 0, font_name = "bananaslip plus", font_size = font_size)
        if label.content_width > self.width:
            font_size = int(font_size / (label.content_width / self.width))
        self._string_sizes[s] = font_size
        return font_size

    def prerender(self):
        for s in self.active_subtitles:
            fs = self.get_font_size(s.text)
            s.get_labels(self.x, self.y, fs)

    def draw(self):
        if self.current_subtitles:
            self.current_subtitles[-1].draw()
