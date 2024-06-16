from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pathlib import Path
    from arcade import Texture

import logging

import arcade
from arcade import Sprite, Text, Sound, color as colors

from charm.lib.anim import perc, ease_circout, lerp
from charm.lib.charm import CharmColors, GumWrapper
from charm.lib.digiview import DigiView, disable_when_focus_lost, shows_errors
from charm.lib.gamemodes.fnf import CameraFocusEvent, FNFEngine, FNFSong
from charm.lib.gamemodes.four_key import FourKeyHighway
from charm.lib.keymap import keymap
from charm.lib.logsection import LogSection
from charm.lib.oggsound import OGGSound
from charm.lib.trackcollection import TrackCollection
from charm.lib.utils import map_range
from charm.objects.lyric_animator import LyricAnimator
from charm.objects.timer import Timer
from charm.views.results import ResultsView

logger = logging.getLogger("charm")


class FNFSongView(DigiView):
    def __init__(self, path: Path, back: DigiView):
        super().__init__(fade_in=1, back=back)
        self.path = path
        self.engine: FNFEngine = None
        self.highway_1: FourKeyHighway = None
        self.highway_2: FourKeyHighway = None
        self.songdata: FNFSong = None
        self.tracks: TrackCollection = None
        self.song_time_text: Text = None
        self.score_text: Text = None
        self.grade_text: Text = None
        self.pause_text: Text = None
        self.dead_text: Text = None
        self.last_camera_event: CameraFocusEvent = None
        self.last_spotlight_position: float = 0
        self.last_spotlight_change: float = 0
        self.go_to_spotlight_position: int = 0
        self.spotlight_position: float = 0
        self.hp_bar_length: float = 250
        self.paused: bool = False
        self.show_text: bool = True
        self.logo_width: int = None
        self.distractions = True
        self.chroma_key = False
        self.camera_events = []
        self.timer = None

        self.success = False

    @shows_errors
    def setup(self) -> None:
        super().presetup()
        with LogSection(logger, "loading song data"):
            path = self.path
            self.songdata = FNFSong.parse(path)
            if not self.songdata:
                raise ValueError("No valid chart found!")

        with LogSection(logger, "loading engine"):
            self.engine = FNFEngine(self.songdata.charts[0])

        with LogSection(logger, "loading highways"):
            self.highway_1 = FourKeyHighway(self.songdata.charts[0], self.engine, (self.window.width / 3 * 2, 0))
            self.highway_2 = FourKeyHighway(self.songdata.charts[1], self.engine, (0, 0), auto = True)

            self.highway_1.bg_color = (0, 0, 0, 0)
            self.highway_2.bg_color = (0, 0, 0, 0)

        with LogSection(logger, "loading sound"):
            soundfiles = [f for f in path.iterdir() if f.is_file() and f.suffix in [".ogg", ".mp3", ".wav"]]
            trackfiles = []
            for s in soundfiles:
                trackfiles.append(OGGSound(s) if s.suffix == ".ogg" else Sound(s))
            self.tracks = TrackCollection(trackfiles)

            self.window.theme_song.volume = 0

        with LogSection(logger, "loading text"):
            self.song_time_text = Text("??:??", (self.size[0] // 2), 10, font_size=24,
                                              anchor_x="center", color=colors.BLACK,
                                              font_name="bananaslip plus")

            self.score_text = Text("0", (self.size[0] // 2), self.size[1] - 10, font_size=24,
                                          anchor_x="center", anchor_y="top", color=colors.BLACK,
                                          font_name="bananaslip plus")

            self.grade_text = Text("Clear", (self.size[0] // 2), self.size[1] - 135, font_size=16,
                                          anchor_x="center", anchor_y="center", color=colors.BLACK,
                                          font_name="bananaslip plus")

            self.pause_text = Text("PAUSED", (self.size[0] // 2), (self.size[1] // 2), font_size=92,
                                          anchor_x="center", anchor_y="center", color=colors.BLACK,
                                          font_name="bananaslip plus")

            self.dead_text = Text("DEAD.", (self.size[0] // 2), (self.size[1] // 3) * 2, font_size=64,
                                         anchor_x="center", anchor_y="center", color=colors.BLACK,
                                         font_name="bananaslip plus")

        with LogSection(logger, "loading gum wrapper"):
            # Generate "gum wrapper" background
            self.gum_wrapper = GumWrapper(self.size)

        with LogSection(logger, "loading judgements"):
            judgement_textures: list[Texture] = [j.get_texture() for j in self.engine.judgements]
            self.judgement_sprite = Sprite(judgement_textures[0])
            self.judgement_sprite.textures = judgement_textures
            self.judgement_sprite.scale = (self.highway_1.w * 0.8) / self.judgement_sprite.width
            self.judgement_sprite.center_x = self.window.width / 2
            self.judgement_sprite.center_y = self.window.height / 4
            self.judgement_jump_pos = self.judgement_sprite.center_y + 25
            self.judgement_land_pos = self.judgement_sprite.center_y
            self.judgement_sprite.alpha = 0

        with LogSection(logger, "creating lyric animations"):
            if self.songdata.lyrics:
                self.lyric_animator = LyricAnimator(self.window.width / 2, self.window.height / 2, self.songdata.lyrics)
                self.lyric_animator.prerender()
            else:
                self.lyric_animator = None

        with LogSection(logger, "finalizing"):
            self.last_camera_event = CameraFocusEvent(0, 2)
            self.last_spotlight_position = 0
            self.last_spotlight_change = 0
            self.go_to_spotlight_position = 0
            self.spotlight_position = 0
            self.camera_events = [e for e in self.songdata.charts[0].events if isinstance(e, CameraFocusEvent)]

            self.hp_bar_length = 250

            self.paused = False
            self.show_text = True

            if self.chroma_key:
                for i in self.highway_1.strikeline:
                    i.alpha = 255
                for i in self.highway_2.strikeline:
                    i.alpha = 255

            self.timer = Timer(250, self.tracks.duration)
            self.timer.center_x = self.window.width // 2
            self.timer.center_y = 25

            self.window.presence.set(f"Playing {self.songdata.metadata.title}")

            self.success = True

        super().postsetup()

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)
        self.highway_1.pos = (self.window.width / 3 * 2, 0)
        self.highway_1.h = self.window.height
        self.highway_2.h = self.window.height
        self.song_time_text.x = (self.window.center_x)
        self.score_text.x = (self.window.center_x)
        self.grade_text.x = (self.window.center_x)
        self.pause_text.x = (self.window.center_x)
        self.dead_text.x = (self.window.center_x)
        self.judgement_sprite.center_x = self.window.center_x
        self.judgement_sprite.center_y = self.window.height / 4

    def on_show_view(self) -> None:
        if not self.success:
            if self.back:
                self.window.show_view(self.back)
            return
        self.tracks.play()
        super().on_show_view()

    @shows_errors
    @disable_when_focus_lost(keyboard=True)
    def on_key_press(self, symbol: int, modifiers: int) -> None:
        super().on_key_press(symbol, modifiers)
        if keymap.back.pressed:
            self.go_back()
        elif keymap.pause.pressed:
            self.paused = not self.paused
            self.tracks.pause() if self.paused else self.tracks.play()
            self.timer.paused = self.paused
        elif keymap.seek_backward.pressed:
            self.tracks.seek(self.tracks.time - 5)
        elif keymap.seek_forward.pressed:
            self.tracks.seek(self.tracks.time + 5)
        elif keymap.log_sync.pressed:
            self.tracks.log_sync()
        elif keymap.toggle_distractions.pressed:
            self.distractions = not self.distractions
        elif keymap.toggle_chroma.pressed:
            self.chroma_key = not self.chroma_key
        elif self.window.debug.enabled and keymap.debug_toggle_hit_window.pressed:
            self.highway_1.show_hit_window = not self.highway_1.show_hit_window
        elif self.window.debug.enabled and keymap.debug_show_results.pressed:
            self.show_results()
        if self.tracks.playing:
            self.engine.on_key_press(symbol, modifiers)

    @shows_errors
    def on_key_release(self, symbol: int, modifiers: int) -> None:
        super().on_key_release(symbol, modifiers)
        if self.tracks.playing:
            self.engine.on_key_release(symbol, modifiers)


    def go_back(self) -> None:
        self.tracks.close()
        super().go_back()

    def show_results(self) -> None:
        self.tracks.close()
        results_view = ResultsView(back=self.back, results=self.engine.generate_results())
        results_view.setup()
        self.window.show_view(results_view)

    @shows_errors
    def on_update(self, delta_time: float) -> None:
        super().on_update(delta_time)
        if self.chroma_key:
            bg_color = colors.BLUE
        elif not self.distractions:
            bg_color = colors.SLATE_GRAY
        else:
            bg_color = CharmColors.FADED_GREEN
        arcade.set_background_color(bg_color)

        if not self.tracks.loaded:
            return

        self.gum_wrapper.on_update(delta_time)

        time = f"{int(self.tracks.time // 60)}:{int(self.tracks.time % 60):02}"
        if self.song_time_text._label.text != time:
            self.song_time_text._label.text = time
        if self.score_text._label.text != str(self.engine.score):
            self.score_text._label.text = str(self.engine.score)

        self.get_spotlight_position(self.tracks.time)

        self.engine.update(self.tracks.time)
        self.engine.calculate_score()
        self.highway_1.update(self.tracks.time)
        self.highway_2.update(self.tracks.time)

        if self.lyric_animator:
            self.lyric_animator.update(self.tracks.time)

        # Judgement
        judgement_index = self.engine.judgements.index(self.engine.latest_judgement) if self.engine.latest_judgement else 0
        judgement_time = self.engine.latest_judgement_time
        if judgement_time:
            self.judgement_sprite.center_y = ease_circout(self.judgement_jump_pos, self.judgement_land_pos, perc(judgement_time, judgement_time + 0.25, self.tracks.time))
            self.judgement_sprite.alpha = int(ease_circout(255, 0, perc(judgement_time + 0.5, judgement_time + 1, self.tracks.time)))
            self.judgement_sprite.set_texture(judgement_index)

        # FC type, etc.
        if self.engine.accuracy is not None:
            if self.grade_text._label.text != f"{self.engine.fc_type} | {round(self.engine.accuracy * 100, 2)}% ({self.engine.grade})":
                self.grade_text._label.text = f"{self.engine.fc_type} | {round(self.engine.accuracy * 100, 2)}% ({self.engine.grade})"

        if self.engine.has_died and not self.window.debug.enabled:
            self.tracks.close()
            self.go_back()

        if self.tracks.tracks and self.tracks.time >= self.tracks.duration:
            self.show_results()

        self.timer.current_time = self.tracks.time
        if self.tracks.time <= 0:
            self.timer._clock = 0  # timer sync
        self.timer.update(delta_time)

    def get_spotlight_position(self, song_time: float) -> None:
        focus_pos = {
            1: 0,
            0: self.window.center_x
        }
        cameraevents = [e for e in self.camera_events if e.time < self.tracks.time + 0.25]
        if cameraevents:
            current_camera_event = cameraevents[-1]
            if self.last_camera_event != current_camera_event:
                self.last_spotlight_change = song_time
                self.last_spotlight_position = self.spotlight_position
                self.go_to_spotlight_position = focus_pos[current_camera_event.focused_player]
                self.last_camera_event = current_camera_event
        self.spotlight_position = ease_circout(self.last_spotlight_position, self.go_to_spotlight_position, perc(self.last_spotlight_change, self.last_spotlight_change + 0.125, song_time))

    def hp_draw(self) -> None:
        hp_min = self.size[0] // 2 - self.hp_bar_length // 2
        hp_max = self.size[0] // 2 + self.hp_bar_length // 2
        hp_normalized = map_range(self.engine.hp, self.engine.min_hp, self.engine.max_hp, 0, 1)
        hp = lerp(hp_min, hp_max, hp_normalized)
        arcade.draw_lrbt_rectangle_filled(
            hp_min, hp_max,
            self.size[1] - 110, self.size[1] - 100,
            colors.BLACK
        )
        arcade.draw_circle_filled(hp, self.size[1] - 105, 20, colors.BLUE)

    def spotlight_draw(self) -> None:
        arcade.draw_lrbt_rectangle_filled(
            self.spotlight_position - self.window.center_x, self.spotlight_position, 0, self.window.height,
            colors.BLACK[:3] + (127,)
        )
        arcade.draw_lrbt_rectangle_filled(
            self.spotlight_position + self.window.center_x, self.spotlight_position + self.window.width, 0, self.window.height,
            colors.BLACK[:3] + (127,)
        )

    @shows_errors
    def on_draw(self) -> None:
        super().predraw()
        # Charm BG
        if self.distractions and not self.chroma_key:
            self.gum_wrapper.draw()

        if self.show_text and not self.chroma_key:
            # self.song_time_text.draw()
            self.score_text.draw()
            self.grade_text.draw()
            if self.engine.has_died:
                self.dead_text.draw()

        if self.paused:
            self.pause_text.draw()

        if not self.chroma_key:
            self.hp_draw()

        self.highway_1.draw()
        self.highway_2.draw()

        if self.distractions and self.camera_events and not self.chroma_key:
            self.spotlight_draw()

        if not self.chroma_key:
            self.judgement_sprite.draw()

        if self.lyric_animator and not self.chroma_key:
            self.lyric_animator.draw()

        self.timer.draw()
        super().postdraw()
