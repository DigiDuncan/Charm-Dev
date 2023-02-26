from dataclasses import dataclass
import importlib.resources as pkg_resources
import logging
from random import randint
import wave

import arcade
from charm.lib.keymap import get_keymap
import nindex
import numpy as np

import charm.data.audio
from charm.lib.adobexml import sprite_from_adobe
from charm.lib.anim import ease_linear, ease_quartout
from charm.lib.digiview import DigiView
from charm.lib.logsection import LogSection
from charm.lib.gamemodes.fnf import FNFEngine, FNFHighway, FNFNote, FNFSong
from charm.lib.paths import songspath
from charm.lib.settings import Settings

logger = logging.getLogger("charm")


@dataclass
class SoundPoint:
    time: float
    amplitude: float


@dataclass
class Beat:
    time: float


colormap = [
    arcade.color.PURPLE,
    arcade.color.CYAN,
    arcade.color.GREEN,
    arcade.color.MAGENTA
]

animationmap = [
    "left",
    "down",
    "up",
    "right"
]

BAD_HARDCODE_TIME = 129.857142857143


class VisualizerView(DigiView):
    def __init__(self, *args, **kwargs):
        super().__init__(fade_in=1, bg_color=arcade.color.BLACK, *args, **kwargs)

    def setup(self):
        super().setup()

        # Load song and get waveform
        with LogSection(logger, "loading song and waveform"):
            with pkg_resources.path(charm.data.audio, "fourth_wall.wav") as p:
                self._song = arcade.Sound(p)
                f = open(p, "rb")
                self.wave = wave.open(f, "rb")
                self.sample_count = self.wave.getnframes()
                self.sample_rate = self.wave.getframerate()
            logger.info(f"Samples loaded: {self.sample_count}")

        self.chart_available = False
        # Create an index of chart notes
        with LogSection(logger, "parsing chart"):
            path = songspath / "fnf" / "fourth-wall"
            self.songdata = FNFSong.parse(path)
        if self.songdata:
            with LogSection(logger, "indexing notes"):
                self.chart_available = True
                self.player_chart = nindex.Index(self.songdata.charts[0].notes, "time")
                enemy_chart = self.songdata.get_chart(2, self.songdata.charts[0].difficulty)
                self.enemy_chart = nindex.Index(enemy_chart.notes, "time")
            with LogSection(logger, "generating highway"):
                self.engine = FNFEngine(self.songdata.charts[0])
                self.highway = FNFHighway(self.songdata.charts[0], self.engine, (((Settings.width // 3) * 2), 0), auto = True)

        # Create background stars
        with LogSection(logger, "creating stars"):
            self.star_camera = arcade.SimpleCamera()
            self.stars = arcade.SpriteList()
            self.scroll_speed = 20  # px/s
            stars_per_screen = 100
            star_height = Settings.height + int(self._song.source.duration * self.scroll_speed)
            star_amount = int(stars_per_screen * (star_height / Settings.height))
            logger.info(f"Generating {star_amount} stars...")
            for i in range(star_amount):
                sprite = arcade.SpriteCircle(5, arcade.color.WHITE, True)
                sprite.center_x = randint(0, Settings.width)
                sprite.center_y = randint(-(star_height - Settings.height), Settings.height)
                self.stars.append(sprite)

        with LogSection(logger, "creating text"):
            self.text = arcade.Text("Fourth Wall by Jacaris", Settings.width / 4, Settings.height * (0.9),
            font_name = "Determination Sans", font_size = 32, align="center", anchor_x="center", anchor_y="center",
            width = Settings.width, color = (255, 255, 255, 128))

        with LogSection(logger, "making gradient"):
            # Gradient
            self.gradient = arcade.shape_list.create_rectangle_filled_with_colors(
                [(-250, Settings.height), (Settings.width + 250, Settings.height), (Settings.width + 250, -250), (-250, -250)],
                [arcade.color.BLACK, arcade.color.BLACK, arcade.color.DARK_PASTEL_PURPLE, arcade.color.DARK_PASTEL_PURPLE]
            )

        with LogSection(logger, "loading sprites"):
            self.scott_atlas = arcade.TextureAtlas((8192, 8192))
            self.sprite_list = arcade.SpriteList(atlas = self.scott_atlas)
            self.sprite = sprite_from_adobe("scott", ("bottom", "left"))
            self.boyfriend = sprite_from_adobe("bfScott", ("bottom", "right"))
            self.sprite_list.append(self.sprite)
            self.sprite_list.append(self.boyfriend)
            self.sprite.cache_textures()
            self.boyfriend.cache_textures()
            self.sprite.bottom = 0
            self.sprite.left = 0
            self.boyfriend.bottom = 0
            self.boyfriend.right = Settings.width - 50
            self.sprite.set_animation("idle")
            self.boyfriend.set_animation("idle")

        # Settings
        with LogSection(logger, "finalizing setup"):
            self.multiplier = 1 / 250
            self.y = Settings.height // 2
            self.line_width = 1
            self.x_scale = 2
            self.resolution = 4
            self.beat_time = 0.5
            self.show_text = True

            # RAM
            self.pixels: list[tuple[int, int]] = [(0, 0) * Settings.width]
            self.last_beat = -self.beat_time
            self.last_enemy_note: FNFNote = None
            self.last_player_note: FNFNote = None
            self.did_harcode = False

            self.window.update_rp("Vs. Scott Cawthon (demo)")

    def on_show(self):
        self.window.theme_song.volume = 0
        self.song = arcade.play_sound(self._song, 1, looping=False)
        super().on_show()

    def on_update(self, delta_time: float):
        super().on_update(delta_time)
        if not self.shown:
            return

        # Waveform
        self.wave.rewind()
        self.wave.setpos(min(int(self.song.time * self.sample_rate), self.sample_count - Settings.width))
        signal_wave = self.wave.readframes(int(Settings.width))
        samples = np.frombuffer(signal_wave, dtype=np.int16)[::self.resolution * 2]
        self.pixels = [(n * self.resolution, float(s) * self.multiplier + self.y) for n, s in enumerate(samples)]

        self.last_beat = self.song.time - (self.song.time % (60 / 72))  # ALSO BAD HARDCODE RN
        enemy_note = self.enemy_chart.lt(self.song.time)
        player_note = self.player_chart.lt(self.song.time)

        if (not self.did_harcode) and self.song.time >= BAD_HARDCODE_TIME:
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
        self.highway.update(self.song.time)

    def on_key_press(self, symbol: int, modifiers: int):
        keymap = get_keymap()
        match symbol:
            case keymap.back:
                self.back.setup()
                self.window.show_view(self.back)
                self.song.delete()
                arcade.play_sound(self.window.sounds["back"])
            case keymap.pause:
                self.song.pause() if self.song.playing else self.song.play()
            case arcade.key.NUM_0:
                self.song.seek(0)
            case arcade.key.T:
                self.show_text = not self.show_text

        return super().on_key_press(symbol, modifiers)

    def on_draw(self):
        self.clear()
        if not self.shown:
            return

        # Camera zoom
        star_zoom = ease_quartout(1, 0.95, self.last_beat, self.last_beat + self.beat_time, self.song.time)
        cam_zoom = ease_quartout(1.05, 1, self.last_beat, self.last_beat + self.beat_time, self.song.time)
        self.star_camera.scale = star_zoom, star_zoom
        self.camera.scale = 1 / cam_zoom, 1 / cam_zoom
        # self.highway.highway_camera.scale = 1 / cam_zoom, 1 / cam_zoom

        # Gradient
        self.gradient.draw()

        # Scroll star camera and draw stars
        self.star_camera.move_to((0, 0 - (self.song.time * self.scroll_speed)))
        self.star_camera.use()
        self.stars.draw()

        self.camera.use()

        # Note flashes
        if self.chart_available:
            player_note = self.player_chart.lt(self.song.time)
            if player_note:
                player_color = colormap[player_note.lane]
                player_time = player_note.time
                player_opacity = ease_linear(32, 0, player_time, player_time + self.beat_time, self.song.time)
                player_color = player_color[:3] + (int(player_opacity),)
                arcade.draw_xywh_rectangle_filled(Settings.width / 2, 0, Settings.width / 2, Settings.height, player_color)
            enemy_note = self.enemy_chart.lt(self.song.time)
            if enemy_note:
                enemy_color = colormap[enemy_note.lane]
                enemy_time = enemy_note.time
                enemy_opacity = ease_linear(32, 0, enemy_time, enemy_time + self.beat_time, self.song.time)
                enemy_color = enemy_color[:3] + (int(enemy_opacity),)
                arcade.draw_xywh_rectangle_filled(0, 0, Settings.width / 2, Settings.height, enemy_color)

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

        super().on_draw()
