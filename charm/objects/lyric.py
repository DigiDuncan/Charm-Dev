from os import PathLike
import re
import arcade

import pysubs2
from pysubs2 import SSAEvent, SSAFile

from charm.lib.generic.song import Seconds

re_karaoke = re.compile(r"{\\(kf?)(\d+)}([^{}]+)")

class Subtitle(SSAEvent):
    def __init__(self, event: SSAEvent, file: SSAFile):
        self._event = event
        self.effect = event.effect
        self.end = event.end
        self.layer = event.layer
        self.marginl = event.marginl
        self.marginr = event.marginr
        self.marginv = event.marginv
        self.marked = event.marked
        self.name = event.name
        self.style = event.style
        self.start = event.start
        self.text = event.text
        self.type = event.type

        self.ssa_style = file.styles[self.style]
        self.start_time: Seconds = self.start / 1000
        self.end_time: Seconds = self.end / 1000
        self.length: Seconds = self.end_time - self.start_time
        self.label = arcade.Text(
            self.plaintext, self.x + self.marginx, self.y + self.marginy,
            color = (self.ssa_style.primarycolor.r, self.ssa_style.primarycolor.g, self.ssa_style.primarycolor.b, 0xFF),
            font_size = self.ssa_style.fontsize // 3,
            font_name = "bananaslip plus",
            bold = self.ssa_style.bold,
            italic = self.ssa_style.italic,
            anchor_x = self.anchor_x,
            anchor_y = self.anchor_y,
            align = self.anchor_x,
            width = arcade.get_window().width
        )

    @property
    def position(self):
        match self.ssa_style.alignment:
            # `alignment` is a number 1-9 in "numpad positioning"
            case 7:
                # top left
                return (0, window.height)
            case 8:
                # top center
                return (window.width / 2, window.height)
            case 9:
                # top right
                return (window.width, window.height)
            case 4:
                # middle left
                return (0, window.height / 2)
            case 5:
                # middle center
                return (window.width / 2, window.height / 2)
            case 6:
                # middle right
                return (window.width, window.height / 2)
            case 1:
                # bottom left
                return (0, 0)
            case 2:
                # bottom center
                return (window.width / 2, 0)
            case 3:
                # bottom right
                return (window.width, 0)

    @property
    def marginx(self):
        if self.ssa_style.alignment in [7, 4, 1]:
            return self.marginl
        elif self.ssa_style.alignment in [9, 6, 3]:
            return -self.marginr
        return 0

    @property
    def marginy(self):
        if self.ssa_style.alignment in [7, 8, 9]:
            return -self.marginv
        elif self.ssa_style.alignment in [1, 2, 3]:
            return self.marginv

    @property
    def x(self):
        return self.position[0]

    @property
    def y(self):
        return self.position[1]

    @property
    def anchor_x(self):
        if self.ssa_style.alignment in [7, 4, 1]:
            return "left"
        elif self.ssa_style.alignment in [8, 5, 2]:
            return "center"
        elif self.ssa_style.alignment in [9, 6, 3]:
            return "right"

    @property
    def anchor_y(self):
        if self.ssa_style.alignment in [7, 8, 9]:
            return "top"
        elif self.ssa_style.alignment in [4, 5, 6]:
            return "center"
        elif self.ssa_style.alignment in [1, 2, 3]:
            return "bottom"

    # When we get to karaoke stuff, this will actually matter.
    def update(self, song_time):
        pass

    def draw(self):
        self.label.draw()


class LyricAnimator:
    def __init__(self, sub_file: PathLike):
        self.subtitles = pysubs2.load(str(sub_file))
        self.active_subtitles = [Subtitle(e, self.subtitles) for e in self.subtitles.events]
        self.current_subtitles: list[Subtitle] = []
        self.song_time = 0

    def update(self, song_time: Seconds):
        self.song_time = song_time
        for subtitle in self.current_subtitles:
            if subtitle.end_time < self.song_time:
                self.current_subtitles.remove(subtitle)
        for subtitle in self.active_subtitles:
            if subtitle.start_time <= self.song_time:
                self.current_subtitles.append(subtitle)
                self.active_subtitles.remove(subtitle)

    def draw(self):
        """Draw all active subtitles."""
        for subtitle in self.current_subtitles:
            subtitle.draw()
