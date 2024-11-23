from dataclasses import dataclass
from importlib.resources import files, as_file
import logging

from random import randint
import wave

import arcade
from arcade import LBWH, SpriteCircle, SpriteList, Text, DefaultTextureAtlas, Camera2D, Sound, color as colors

import numpy as np
import nindex

import charm.data.audio
from charm.core.keymap import KeyMap
from charm.lib.adobexml import sprite_from_adobe
from charm.lib.anim import ease_linear, ease_quartout, perc
from charm.core.digiview import DigiView, disable_when_focus_lost, shows_errors
from charm.lib.logsection import LogSection
from charm.core.paths import songspath
from charm.lib.trackcollection import TrackCollection

from charm.game.generic import AutoEngine, ChartSet
from charm.game.gamemodes.fnf import FNFNote
from charm.game.gamemodes.four_key import FourKeyHighway
from charm.game.parsers.fnf import FNFParser


logger = logging.getLogger("charm")


@dataclass
class SoundPoint:
    time: float
    amplitude: float


@dataclass
class Beat:
    time: float


colormap = [
    colors.PURPLE,
    colors.CYAN,
    colors.GREEN,
    colors.MAGENTA
]

animationmap = [
    "left",
    "down",
    "up",
    "right"
]

# TODO: FIX ME OH GOD
# OK, so this is just "when Scott is supposed to make the phone animation"
# Investigate:
# Is this encoded in the chart?
# Is it encoded in a way that we can reliably use this information in other charts?
# Is it worth adding this functionality to Charm, or should this be an injector?
BAD_HARDCODE_TIME = 129.857142857143


class VisualizerView(DigiView):
    def __init__(self, back: DigiView):
        super().__init__(fade_in=1, back=back)

    @shows_errors
    def setup(self) -> None:
        super().presetup()
        arcade.set_background_color(colors.BLACK)

        # Load song and get waveform
        with LogSection(logger, "loading song and waveform"):
            with as_file(files(charm.data.audio) / "fourth_wall.wav") as p:
                self._song = Sound(p)
                self.tracks = TrackCollection([self._song])
                f = open(p, "rb")
                self.wave = wave.open(f, "rb")
                self.sample_count = self.wave.getnframes()
                self.sample_rate = self.wave.getframerate()
            logger.info(f"Samples loaded: {self.sample_count}")

        self.chart_available = False
        # Create an index of chart notes
        with LogSection(logger, "parsing chart"):
            path = songspath / "fnf" / "funkin-at-freddys" / "fourth-wall"
            try:
                charts = FNFParser.parse_chart_metadata(path)
                metadata = FNFParser.parse_chartset_metadata(path)
                self.chartset = ChartSet(path, metadata, charts)
            except Exception as e:
                logger.error(e)
                self.chartset = None
            else:
                with LogSection(logger, "indexing notes"):
                    self.chart_available = True
                    self.player_chart, self.enemy_chart = FNFParser.parse_chart(self.chartset.charts[0])
                    self.player_notes = nindex.Index(self.player_chart.notes, 'time')
                    self.enemy_notes = nindex.Index(self.enemy_chart.notes, 'time')
                with LogSection(logger, "generating highway"):
                    self.engine = AutoEngine(self.player_chart)
                    self.highway = FourKeyHighway(self.player_chart, self.engine, (((self.window.width // 3) * 2), 0))
                    self.highway.bg_color = colors.TRANSPARENT_BLACK

        # Create background stars
        with LogSection(logger, "creating stars"):
            self.star_camera = Camera2D()
            self.stars = SpriteList()
            self.scroll_speed = 20  # px/s
            stars_per_screen = 100
            star_height = self.window.height + int(self._song.source.duration * self.scroll_speed)
            star_amount = int(stars_per_screen * (star_height / self.window.height))
            logger.info(f"Generating {star_amount} stars...")
            for _ in range(star_amount):
                sprite = SpriteCircle(5, colors.WHITE, True)
                sprite.center_x = randint(0, self.window.width)
                sprite.center_y = randint(-(star_height - self.window.height), self.window.height)
                self.stars.append(sprite)

        with LogSection(logger, "creating text"):
            self.text = Text("Fourth Wall by Jacaris", self.window.width / 4, self.window.height * (0.9),
                                    font_name = "bananaslip plus", font_size = 32, align="center",
                                    anchor_x="center", anchor_y="center",
                                    width = self.window.width, color = (255, 255, 255, 128))

        with LogSection(logger, "making gradient"):
            # Gradient
            self.gradient = arcade.shape_list.create_rectangle_filled_with_colors(
                [(-250, self.window.height), (self.window.width + 250, self.window.height), (self.window.width + 250, -250), (-250, -250)],
                [colors.BLACK, colors.BLACK, colors.DARK_PASTEL_PURPLE, colors.DARK_PASTEL_PURPLE]
            )

        with LogSection(logger, "loading sprites"):
            self.scott_atlas = DefaultTextureAtlas((8192, 8192))
            self.sprite_list = SpriteList(atlas = self.scott_atlas)
            self.sprite = sprite_from_adobe("scott", ("bottom", "left"))
            self.boyfriend = sprite_from_adobe("bfScott", ("bottom", "right"))
            self.sprite_list.append(self.sprite)
            self.sprite_list.append(self.boyfriend)
            self.sprite.cache_textures()
            self.boyfriend.cache_textures()
            self.sprite.bottom = 0
            self.sprite.left = 0
            self.boyfriend.bottom = 0
            self.boyfriend.right = self.window.width - 50
            self.sprite.set_animation("idle")
            self.boyfriend.set_animation("idle")

        # Settings
        with LogSection(logger, "finalizing setup"):
            self.multiplier = 1 / 250
            self.y = self.window.height // 2
            self.line_width = 1
            self.x_scale = 2
            self.resolution = 4
            self.beat_time = 0.5
            self.show_text = False

            # RAM
            self.pixels: list[tuple[int, int]] = [(0, 0) * self.window.width]
            self.last_beat = -self.beat_time
            self.last_enemy_note: FNFNote = None
            self.last_player_note: FNFNote = None
            self.did_harcode = False

            self.window.presence.set("Vs. Scott Cawthon (demo)")

        super().postsetup()

    @shows_errors
    def on_show_view(self) -> None:
        self.window.theme_song.volume = 0
        self.tracks.start()
        super().on_show_view()

    @shows_errors
    def on_update(self, delta_time: float) -> None:
        super().on_update(delta_time)
        if not self.shown:
            return
        self.tracks.validate_playing()

        # Waveform
        self.wave.rewind()
        self.wave.setpos(min(int(self.tracks.time * self.sample_rate), self.sample_count - self.window.width))
        signal_wave = self.wave.readframes(int(self.window.width))
        samples = np.frombuffer(signal_wave, dtype=np.int16)[::self.resolution * 2]
        self.pixels = [(n * self.resolution, float(s) * self.multiplier + self.y) for n, s in enumerate(samples)]

        self.last_beat = self.tracks.time - (self.tracks.time % (60 / 72))  # ALSO BAD HARDCODE RN
        enemy_note = self.enemy_notes.lt(self.tracks.time)
        player_note = self.player_notes.lt(self.tracks.time)

        if (not self.did_harcode) and self.tracks.time >= BAD_HARDCODE_TIME:
            # Y'know?
            self.sprite.play_animation_once("phone")
            self.did_harcode = True
        if enemy_note and self.last_enemy_note is not enemy_note:
            self.sprite.play_animation_once(animationmap[enemy_note.lane])
            self.last_enemy_note = enemy_note
        if player_note and self.last_player_note is not player_note:
            self.boyfriend.play_animation_once(animationmap[player_note.lane])
            self.last_player_note = player_note

        self.sprite.update_animation(delta_time)
        self.boyfriend.update_animation(delta_time)
        self.engine.update(self.tracks.time)
        self.engine.calculate_score()
        self.highway.update(self.tracks.time)

    @shows_errors
    def on_button_press(self, keymap: KeyMap) -> None:
        if keymap.back.pressed:
            self.go_back()
        elif keymap.pause.pressed:
            self.tracks.pause() if self.tracks.playing else self.tracks.play()
        elif keymap.seek_zero.pressed:
            raise NotImplementedError
        elif keymap.toggle_show_text.pressed:
            self.show_text = not self.show_text

    def go_back(self) -> None:
        self.tracks.pause()
        super().go_back()

    @shows_errors
    def on_draw(self) -> None:
        super().predraw()
        if not self.shown:
            return

        # Camera zoom
        star_zoom = ease_quartout(1, 0.95, perc(self.last_beat, self.last_beat + self.beat_time, self.tracks.time))
        cam_zoom = ease_quartout(1.05, 1, perc(self.last_beat, self.last_beat + self.beat_time, self.tracks.time))
        self.star_camera.zoom = star_zoom
        self.window.camera.zoom = cam_zoom
        # self.highway.highway_camera.scale = 1 / cam_zoom, 1 / cam_zoom

        self.window.camera.use()  # TODO: Create Camera2D inside this view don't use the window's

        # Gradient
        self.gradient.draw()

        # Scroll star camera and draw stars
        self.star_camera.position = (self.window.center_x, 0 - (self.tracks.time * self.scroll_speed))
        with self.star_camera.activate():
            self.stars.draw()

        # Note flashes
        if self.chart_available:
            player_note = self.player_notes.lt(self.tracks.time)
            if player_note:
                player_color = colormap[player_note.lane]
                player_time = player_note.time
                player_opacity = ease_linear(32, 0, perc(player_time, player_time + self.beat_time, self.tracks.time))
                player_color = player_color[:3] + (int(player_opacity),)
                arcade.draw_rect_filled(LBWH(self.window.width / 2, 0, self.window.width / 2, self.window.height), player_color)
            enemy_note = self.enemy_notes.lt(self.tracks.time)
            if enemy_note:
                enemy_color = colormap[enemy_note.lane]
                enemy_time = enemy_note.time
                enemy_opacity = ease_linear(32, 0, perc(enemy_time, enemy_time + self.beat_time, self.tracks.time))
                enemy_color = enemy_color[:3] + (int(enemy_opacity),)
                arcade.draw_rect_filled(LBWH(0, 0, self.window.width / 2, self.window.height), enemy_color)

        # Text
        if self.show_text:
            self.text.draw()

        line_color = (0, 255, 255, 255)
        line_outline_color = (255, 255, 255, 255)
        arcade.draw_line_strip(self.pixels, line_outline_color, self.line_width + 2)
        arcade.draw_line_strip(self.pixels, line_color, self.line_width)

        if self.chart_available:
            self.sprite_list.draw()
            self.highway.draw()

        self.window.camera.zoom = 1.0
        self.window.camera.use()
        super().postdraw()
