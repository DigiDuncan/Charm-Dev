from copy import copy

import arcade

import pyglet
from pyglet import gl

from charm.lib.types import Seconds
from charm.objects.emojilabel import FormattedLabel, update_emoji_doc


gl.glEnable(gl.GL_DEPTH_TEST)


class LyricEvent:
    def __init__(self, time: Seconds, length: Seconds, text: str, karaoke: str = ""):
        self.time = time
        self.length = length
        self.text = text
        self.karaoke = karaoke


    @property
    def end_time(self) -> Seconds:
        return self.time + self.length

    @end_time.setter
    def end_time(self, v: Seconds) -> None:
        self.length = v - self.time


class LyricAnimator:
    def __init__(self, x: float, y: float, events: list[LyricEvent] | None = None, width: int | None = None) -> None:
        self._ctx = arcade.get_window().ctx

        self.x = x
        self.y = y
        if width is None:
            width = int(arcade.get_window().width * 0.9)
        self.width = width
        self.max_font_size = 24

        if events is None:
            events = []
        self.events = events
        self.active_subtitles = (e for e in sorted((copy(e) for e in self.events), key=lambda e: e.time))
        self.next_subtitle = next(self.active_subtitles, None)
        self.current_subtitles: list[LyricEvent] = []

        self.song_time = 0

        self.show_box = True

        self._string_sizes: dict[str, int] = {}

        self._test_label: FormattedLabel = FormattedLabel("test", font_name = "bananaslip plus", font_size=self.max_font_size, align = "center", anchor_x = "center",)

        self._label_batch: pyglet.graphics.Batch = pyglet.graphics.Batch()

        self._shadow_label: FormattedLabel = FormattedLabel("shadow", x = self.x + 2, y = self.y - 2, z = 10, font_name = "bananaslip plus", font_size = self.max_font_size, color = (0, 0, 0, 127), align = "center", anchor_x = "center",
                                                            batch=self._label_batch, group=pyglet.graphics.Group(order=0))
        self._under_label: FormattedLabel = FormattedLabel("under", x = self.x, y = self.y, z = 20, font_name = "bananaslip plus", font_size = self.max_font_size, color = (0, 0, 0, 255), align = "center", anchor_x = "center",
                                                           batch = self._label_batch, group=pyglet.graphics.Group(order=1))
        self._over_label: FormattedLabel = FormattedLabel("over", x = self.x, y = self.y, z = 30, font_name = "bananaslip plus", font_size = self.max_font_size, color = (255, 255, 0, 255), align = "left", anchor_x = "left",
                                                          batch = self._label_batch, group=pyglet.graphics.Group(order=2))
        self._shown_event: LyricEvent = None

    def update(self, song_time: Seconds) -> None:
        self.song_time = song_time
        for subtitle in self.current_subtitles:
            if subtitle.end_time < self.song_time:
                self.current_subtitles.remove(subtitle)

        if self.next_subtitle is not None and self.next_subtitle.time <= self.song_time:
            self.current_subtitles.append(self.next_subtitle)
            self.next_subtitle = next(self.active_subtitles, None)

        if not self.current_subtitles:
            self._clear_subtitles()
            self._shown_event = None

        elif self.current_subtitles[-1] != self._shown_event:
            self._update_subtitles(self.current_subtitles[-1])
            self._shown_event = self.current_subtitles[-1]

    def _clear_subtitles(self):
        self._shadow_label.position = -1000.0, -1000.0, 10
        self._under_label.position = -1000.0, -1000.0, 20
        self._over_label.position = -1000.0, -1000.0, 30

    def _update_subtitles(self, subtitle: LyricEvent):
        fs = self.get_font_size(subtitle.text)
        if self._shadow_label.font_size != fs:
            self._shadow_label.set_style('font_size', fs)
            self._under_label.set_style('font_size', fs)
            self._over_label.set_style('font_size', fs)

        if self._shown_event is None or self._shown_event.text != subtitle.text:
            self._shadow_label.document = update_emoji_doc(self._shadow_label.document, subtitle.text, fs, "twemoji-shadow")
            self._shadow_label.position = self.x + 2, self.y - 2, 10

            self._under_label.document = update_emoji_doc(self._under_label.document, subtitle.text, fs, "twemoji-bw" if subtitle.karaoke else "twemoji")
            self._under_label.position = self.x, self.y, 20

        self._over_label.document = update_emoji_doc(self._over_label.document, subtitle.karaoke, fs, 'twemoji')
        self._over_label.position = self.x - self._under_label.content_width // 2, self.y, 30

    def get_font_size(self, s: str) -> int:
        if s in self._string_sizes:
            return self._string_sizes[s]
        font_size = self.max_font_size
        self._test_label.document = update_emoji_doc(self._test_label.document, s, font_size)
        if self._test_label.content_width > self.width:
            font_size = int(font_size / (self._test_label.content_width / self.width))
        self._string_sizes[s] = font_size
        return font_size

    def prerender(self) -> None:
        # This forces the generation of expensive regex removing a lag spike
        self._update_subtitles(self.next_subtitle)
        self.get_font_size(":wave:")
        self._label_batch.draw()

    def draw(self) -> None:
        if self.current_subtitles:
            self._label_batch.draw()
            # self.current_subtitles[-1].draw()
