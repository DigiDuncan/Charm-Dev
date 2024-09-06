from __future__ import annotations

from typing import TYPE_CHECKING

from arcade import get_window, color, load_texture, draw_sprite, Text, Sprite, Texture
from arcade.types import Color, Point
from nindex.index import Index

from charm.lib.anim import perc, ease_circout
from charm.lib.displayables import Countdown, Spotlight, HPBar, Timer
from charm.lib.types import Seconds
from charm.objects.lyric_animator import LyricAnimator, LyricEvent

from charm.core.generic.chart import CountdownEvent
from charm.core.generic.engine import Engine, AutoEngine
from charm.core.generic.display import Display

from charm.core.gamemodes.four_key.chart import FourKeyChart
from charm.core.gamemodes.fnf.chart import CameraFocusEvent
from charm.core.gamemodes.fnf.engine import FNFEngine
from charm.core.gamemodes.fnf.highway import FNFHighway

# TODO: turn into actually using skin manager :3
from importlib.resources import files
import charm.data.images.skins as skins

if TYPE_CHECKING:
    from charm.lib.digiwindow import DigiWindow

class FNFDisplay(Display[FNFEngine, FourKeyChart]):

    def __init__(self, engine: FNFEngine, charts: tuple[FourKeyChart, ...]):
        super().__init__(engine, charts)
        self._win: DigiWindow = get_window()
        assert len(charts) == 2, "FNF expects two charts. [0] for the player, [1] for the opposition"
        self.player_chart: FourKeyChart
        self.opp_chart: FourKeyChart
        self.player_chart, self.opp_chart = charts

        # TODO: make more flexible post mvp
        self._enemy_engine: Engine = AutoEngine(charts[1], 0.0)

        # NOTE: change highways to work of their center position not bottom left
        # TODO: place highways at true ideal locations
        self._player_highway: FNFHighway = FNFHighway(self.player_chart, engine, (0, 0))
        self._player_highway.pos = (self._win.width - self._player_highway.w - 25, 0)
        self._player_highway.bg_color = Color(0, 0, 0, 0)
        self._enemy_highway: FNFHighway = FNFHighway(self.opp_chart, self._enemy_engine, (0, 0))
        self._enemy_highway.pos = (25, 0)
        self._enemy_highway.bg_color = Color(0, 0, 0, 0)

        # -- Text Objects --
        self.show_text: bool = True
        self._overlay_text: Text = Text("PAUSE", self._win.center_x, self._win.center_y, font_size=92,
                                        anchor_x="center", color=color.BLACK,
                                        font_name="bananaslip plus")
        self._score_text: Text = Text("0", self._win.center_x, self._win.height - 10, font_size=24,
                                    anchor_x="center", anchor_y="top", color=color.BLACK,
                                    font_name="bananaslip plus")
        self._grade_text: Text = Text("Clear", self._win.center_x, self._win.height - 135, font_size=16,
                                      anchor_x="center", anchor_y="center", color=color.BLACK,
                                      font_name="bananaslip plus")

        # -- Judgement --
        # TODO: move to skinning eventually [post mvp]
        self._judgement_textures: dict[str, Texture] = {
            judgement.key: load_texture(files(skins) / "fnf" / f"judgement-{judgement.key}.png")
            for judgement in self.engine.judgements
        }

        self._judgement_sprite: Sprite = Sprite(self._judgement_textures[self.engine.judgements[0].key])
        self._judgement_sprite.scale = 0.8 * (self._player_highway.w / self._judgement_sprite.width)
        self._judgement_sprite.alpha = 0
        self._judgement_jump: float = self._win.center_y * 0.333 + 25
        self._judgement_land: float = self._win.center_y * 0.333
        self._judgement_sprite.center_x = self._win.center_x

        if lyrics := self.player_chart.events_by_type(LyricEvent):
            self.lyric_animator: LyricAnimator = LyricAnimator(self._win.width / 2, self._win.height / 2, lyrics)
            self.lyric_animator.prerender()
        else:
            self.lyric_animator: LyricAnimator = None

        # -- Camera Events
        if camera_events := self.player_chart.events_by_type(CameraFocusEvent):
            self.spotlight = Spotlight(camera_events)
            self.spotlight.last_camera_event = CameraFocusEvent(0, 2)
        else:
            self.spotlight = None

        # HP
        self.hp_bar = HPBar(self._win.center_x, self._win.height * 0.75, 10, 250, self.engine)

        # Timer, although the timer was not used in fnfsong
        # EDIT: This is a lie. -- Digi
        self.timer = Timer(250, 60)
        self.timer.center_x = self._win.center_x
        self.timer.center_y = 20

        if countdowns := self.player_chart.events_by_type(CountdownEvent):
            self.countdowns = Index(countdowns, "time")
            self.countdown = Countdown(self._player_highway.x + self._player_highway.w / 2, self._win.center_y, self._player_highway.w / 2)
        else:
            self.countdown: Countdown = None

    def pause(self) -> None:
        if not self.engine.has_died:
            self._overlay_text.text = "PAUSE"

    def unpause(self) -> None:
        self._overlay_text.text = ""

    def update(self, song_time: Seconds) -> None:
        self._song_time = song_time

        if self._score_text.text != str(self.engine.score):
            self._score_text.text = str(self.engine.score)

        self._enemy_engine.update(song_time)
        self._enemy_engine.calculate_score()

        self._player_highway.update(song_time)
        self._enemy_highway.update(song_time)

        if self.engine.latest_judgement_time:
            time = self.engine.latest_judgement_time
            self._judgement_sprite.texture = self._judgement_textures[self.engine.latest_judgement.key]
            self._judgement_sprite.center_y = ease_circout(self._judgement_jump, self._judgement_land, perc(time, time + 0.25, song_time))
            self._judgement_sprite.alpha = int(ease_circout(255, 0, perc(time + 0.5, time + 1, song_time)))

        if self.engine.accuracy is not None:
            self._grade_text.text = f"{self.engine.fc_type} | {round(self.engine.accuracy * 100, 2)}% ({self.engine.grade})"

        self.timer.current_time = song_time
        self.timer.update(self._win.delta_time)

        if self.spotlight:
            self.spotlight.update(song_time)

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

        self._player_highway.draw()
        self._enemy_highway.draw()

        if self.spotlight:
            self.spotlight.draw()

        self.hp_bar.draw()
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

    def debug_fetch_note_sprites_at_point(self, point: Point) -> list:
        # TODO: NOT HERE
        from arcade.sprite_list.collision import get_sprites_at_point

        player_notes = get_sprites_at_point(point, self._player_highway._note_pool._source)
        enemy_notes = get_sprites_at_point(point, self._enemy_highway._note_pool._source)
        return player_notes + enemy_notes
