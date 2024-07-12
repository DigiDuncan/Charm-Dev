from copy import copy

import arcade

import pyglet
from pyglet import gl

from charm.lib.types import Seconds
from charm.objects.emojilabel import EmojiLabel, FormattedLabel, update_emoji_doc

import cProfile


gl.glEnable(gl.GL_DEPTH_TEST)


class LyricEvent:
    def __init__(self, time: Seconds, length: Seconds, text: str, karaoke: str = ""):
        self.time = time
        self.length = length
        self.text = text
        self.karaoke = karaoke

        self._labels: list[EmojiLabel] = []
        self.labels: list[EmojiLabel] = []

    @property
    def end_time(self) -> Seconds:
        return self.time + self.length

    @end_time.setter
    def end_time(self, v: Seconds) -> None:
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

    def update_labels(self, shadow: EmojiLabel, under: EmojiLabel, over: EmojiLabel, x: float, y: float, font_size: int) -> None:
        default_emoji_set = "twemoji-bw" if self.karaoke else "twemoji"
        shadow.document = generate_emoji_doc(self.text, font_size, "twemoji-shadow")
        shadow.position = x + 2, y - 2, 3
        under.document = generate_emoji_doc(self.text, font_size, default_emoji_set)
        under.position = x, y, 2
        if self.karaoke:
            over.document = generate_emoji_doc(self.text, font_size, "twemoji")
        else:
            over.document = generate_emoji_doc("", font_size, "twemoji")
        over.position = x, y, 1

        self.labels = [shadow, under, over]


class LyricAnimator:
    def __init__(self, x: float, y: float, events: list[LyricEvent] | None = None, width: int | None = None) -> None:
        self.x = x
        self.y = y
        if width is None:
            width = int(arcade.get_window().width * 0.9)
        self.width = width
        self.max_font_size = 24

        if events is None:
            events = []
        self.events = events
        self.active_subtitles = [copy(e) for e in self.events]
        self.current_subtitles: list[LyricEvent] = []

        self.song_time = 0

        self.show_box = True

        self._string_sizes: dict[str, int] = {}

        self._test_label: FormattedLabel = FormattedLabel("test", font_name = "bananaslip plus", font_size=self.max_font_size, align = "center", anchor_x = "center",)

        self._label_batch: pyglet.graphics.Batch = pyglet.graphics.Batch()

        self._shadow_label: FormattedLabel = FormattedLabel("shadow", x = -1000, y = -1000, z = 3, font_name = "bananaslip plus", font_size = self.max_font_size, color = (0, 0, 0, 127), align = "center", anchor_x = "center", batch = self._label_batch)
        self._under_label: FormattedLabel = FormattedLabel("under", x = -1000, y = -1000, z = 2, font_name = "bananaslip plus", font_size = self.max_font_size, color = (0, 0, 0, 255), align = "center", anchor_x = "center", batch = self._label_batch)
        self._over_label: FormattedLabel = FormattedLabel("over", x = -1000, y = -1000, z = 1, font_name = "bananaslip plus", font_size = self.max_font_size, color = (255, 255, 0, 255), align = "left", anchor_x = "left", batch = self._label_batch)
        self._shown_event: LyricEvent = None

    def update(self, song_time: Seconds) -> None:
        self.song_time = song_time
        for subtitle in self.current_subtitles:
            if subtitle.end_time < self.song_time:
                self.current_subtitles.remove(subtitle)

        for subtitle in self.active_subtitles:
            if subtitle.time <= self.song_time:
                self.current_subtitles.append(subtitle)
                self.active_subtitles.remove(subtitle)

        if not self.current_subtitles:
            self._shown_event = None

            self._shadow_label.position = -1000.0, -1000.0, 3
            self._under_label.position = -1000.0, -1000.0, 2
            self._over_label.position = -1000.0, -1000.0, 1
        elif self.current_subtitles[-1] != self._shown_event:
            self._shown_event = subtitle = self.current_subtitles[-1]

            fs = self.get_font_size(subtitle.text)
            self._shadow_label.document = update_emoji_doc(self._shadow_label.document, subtitle.text, fs, "twemoji-shadow")
            self._shadow_label.position = self.x + 2, self.y - 2, 3
            self._under_label.document = update_emoji_doc(self._under_label.document, subtitle.text, fs, "twemoji-bw" if subtitle.karaoke else "twemoji")
            self._under_label.position = self.x, self.y, 2
            if subtitle.karaoke:
                self._over_label.document = update_emoji_doc(self._over_label.document, subtitle.karaoke, fs, 'twemoji')
                self._over_label.position = self.x - self._under_label.content_width // 2, self.y, 1
            else:
                self._over_label.position = -1000.0, -1000.0, 1

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
        # TODO: doesn't work lmao
        self.get_font_size(":wave:")
        self._label_batch.draw()
        return
        with cProfile.Profile() as pr:
            for s in self.active_subtitles:
                fs = self.get_font_size(s.text)
                s.get_labels(self.x, self.y, fs)
        pr.print_stats('time')

    def draw(self) -> None:
        if self.current_subtitles:
            self._label_batch.draw()
            # TODO: BAD BAD BAD, but the shadow keeps going above the others so ¯\_(ツ)_/¯
            self._over_label.draw()
            # self.current_subtitles[-1].draw()
