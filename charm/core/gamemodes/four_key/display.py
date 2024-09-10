from __future__ import annotations
from typing import TYPE_CHECKING

from charm.core.generic.sprite import NoteSprite
if TYPE_CHECKING:
    from charm.lib.digiview import DigiWindow
from collections.abc import Sequence

from importlib.resources import files

from arcade import Sprite, Text, Texture, draw_sprite, get_window, load_texture
from arcade import color
from nindex.index import Index

from charm.lib.anim import ease_circout, perc
from charm.lib.displayables import Countdown, Timer
from charm.lib.types import Point, Seconds
from charm.objects.lyric_animator import LyricAnimator, LyricEvent

from charm.core.generic import CountdownEvent, Display
from charm.core.gamemodes.fnf.engine import FNFEngine
from .chart import FourKeyChart
from .engine import FourKeyEngine
from .highway import FourKeyHighway

import charm.data.images.skins as skins


class FourKeyDisplay(Display):
    def __init__(self, engine: FNFEngine | FourKeyEngine, charts: Sequence[FourKeyChart]):
        super().__init__(engine, charts)
        self.engine: FNFEngine | FourKeyEngine
        self.charts: Sequence[FourKeyChart]
        self._win: DigiWindow = get_window()  # type: ignore | aaa shut up Arcade
        self.chart = charts[0]

        # NOTE: change highways to work of their center position not bottom left
        ONE_THIRD_W = self._win.width // 3
        self._highway = FourKeyHighway(self.chart, self.engine, (self._win.center_x - ONE_THIRD_W, 0), (ONE_THIRD_W, self._win.height))

        # -- Text Objects --
        self.show_text: bool = True
        self._score_text: Text = Text("0", self._win.center_x + ONE_THIRD_W, self._win.height - 10, font_size=48,
                                    anchor_x="center", anchor_y="top", color=color.BLACK,
                                    font_name="bananaslip plus")
        self._grade_text: Text = Text("Clear", self._win.center_x + ONE_THIRD_W, self._win.height - 135, font_size=16,
                                      anchor_x="center", anchor_y="center", color=color.BLACK,
                                      font_name="bananaslip plus")

        # -- Judgement --
        # TODO: move to skinning eventually [post mvp]
        self._judgement_textures: dict[str, Texture] = {
            judgement.key: load_texture(files(skins) / "base" / f"judgement-{judgement.key}.png")
            for judgement in self.engine.judgements
        }

        self._judgement_sprite: Sprite = Sprite(self._judgement_textures[self.engine.judgements[0].key])
        self._judgement_sprite.scale = 0.8 * (self._highway.w / self._judgement_sprite.width)
        self._judgement_sprite.alpha = 0
        self._judgement_jump: float = self._win.center_y + 25
        self._judgement_land: float = self._win.center_y
        self._judgement_sprite.center_x = self._win.center_x + ONE_THIRD_W
        self._judgement_sprite.center_y = self._win.center_y

        if lyrics := self.chart.events_by_type(LyricEvent):
            self.lyric_animator: LyricAnimator = LyricAnimator(self._win.width / 2, self._win.height / 2, lyrics)
            self.lyric_animator.prerender()
        else:
            self.lyric_animator: LyricAnimator = None

        # HP
        # self.hp_bar = HPBar(self._win.center_x, self._win.height * 0.75, 10, 250, self.engine)

        # Timer
        self.timer = Timer(250, 60)
        self.timer.center_x = self._win.center_x + ONE_THIRD_W
        self.timer.center_y = 60

        # Countdowns
        if countdowns := self.chart.events_by_type(CountdownEvent):
            self.countdowns = Index(countdowns, "time")
            self.countdown = Countdown(self._highway.x + self._highway.w / 2, self._win.center_y, self._highway.w / 2)
        else:
            self.countdown: Countdown = None

        self._overlay_text: Text = Text("PAUSE", self._win.center_x, self._win.center_y, font_size=92,
                                        anchor_x="center", color=color.BLACK,
                                        font_name="bananaslip plus")

    def pause(self) -> None:
        if not self.engine.has_died:
            self._overlay_text.text = "PAUSE"

    def unpause(self) -> None:
        self._overlay_text.text = ""

    def update(self, song_time: Seconds) -> None:
        self._song_time = song_time

        if self._score_text.text != str(self.engine.score):
            self._score_text.text = str(self.engine.score)

        self._highway.update(song_time)

        if self.engine.latest_judgement_time:
            time = self.engine.latest_judgement_time
            self._judgement_sprite.texture = self._judgement_textures[self.engine.latest_judgement.key]
            self._judgement_sprite.center_y = ease_circout(self._judgement_jump, self._judgement_land, perc(time, time + 0.25, song_time))
            self._judgement_sprite.alpha = int(ease_circout(255, 0, perc(time + 0.5, time + 1, song_time)))

        if self.engine.accuracy is not None:
            self._grade_text.text = f"{self.engine.fc_type} | {round(self.engine.accuracy * 100, 2)}% ({self.engine.grade})"

        self.timer.current_time = song_time
        self.timer.update(self._win.delta_time)

        if self.lyric_animator:
            self.lyric_animator.update(song_time)

        if self.countdown:
            self.countdown.update(song_time)
            next_countdown = self.countdowns.lteq(song_time)
            if next_countdown is not None and self.countdown.start_time != next_countdown.time:
                self.countdown.use(next_countdown.time, next_countdown.length)

    def draw(self) -> None:
        if self.show_text:
            self._score_text.draw()
            if self.engine.has_died:
                self._overlay_text.text = "DEAD"
            self._overlay_text.draw()

        self._highway.draw()

        # self.hp_bar.draw()
        self.timer.draw()

        self._grade_text.draw()

        if self.lyric_animator:
            self.lyric_animator.draw()

        if self.countdown:
            self.countdown.draw()

        draw_sprite(self._judgement_sprite)

    def resize(self, width: int, height: int) -> None:
        # ! TODO
        pass

    def debug_fetch_note_sprites_at_point(self, point: Point) -> list[NoteSprite]:
        # TODO: NOT HERE
        from arcade.sprite_list.collision import get_sprites_at_point

        notes = get_sprites_at_point(point, self._highway._note_pool._source)
        return notes
