from __future__ import annotations

import getpass
import importlib.resources as pkg_resources
import random
from types import ModuleType
from typing import cast

import arcade
import imgui
import pyglet

import charm.data.audio
import charm.data.images
from charm.lib.anim import ease_linear, ease_quadinout
from charm.lib.charm import CharmColors, move_gum_wrapper
from charm.lib.digiview import DigiView, ignore_imgui, shows_errors
from charm.lib.digiwindow import Eggs
from charm.lib.keymap import keymap
from charm.lib.settings import settings
from charm.lib.utils import img_from_resource, typewriter
from charm.views.mainmenu import MainMenuView
from charm.lib.keymap import keymap

FADE_DELAY = 1
SWITCH_DELAY = 0.5 + FADE_DELAY


class TitleView(DigiView):
    def __init__(self):
        super().__init__(
            bg_color=CharmColors.FADED_GREEN,
            destinations={"mainmenu": MainMenuView(back=self)}
        )
        self.logo: arcade.Sprite
        self.dumb_fix_for_logo_pos: bool
        self.main_sprites: arcade.SpriteList[arcade.Sprite]
        self.goto_fade_time: float | None
        self.goto_switch_time: float | None
        self.splash_label: SplashLogo | ClownLogo
        self.show_clown: bool = self.window.egg_roll == Eggs.TRICKY
        self.song_label: SongLabel
        self.press_label: PressLabel

    @shows_errors
    def setup(self) -> None:
        self.goto_fade_time = None
        self.goto_switch_time = None

        self.window.theme_song.seek(self.local_time + 3)

        arcade.set_background_color(CharmColors.FADED_GREEN)
        self.main_sprites = arcade.SpriteList()

        # Set up main logo
        logo_img = img_from_resource(cast(ModuleType, charm.data.images), "logo.png")
        logo_texture = arcade.Texture(logo_img)
        self.logo = arcade.Sprite(logo_texture)

        self.main_sprites.append(self.logo)

        self.splash_label = self.generate_splash()
        self.splash_label.random_splash()

        # Song details
        self.song_label = SongLabel()

        # Press start prompt
        self.press_label = PressLabel(x=self.window.width // 2, y=self.window.height // 4)

        self.welcome_label = arcade.Text(f"welcome, {getpass.getuser()}!",
                                         font_name='bananaslip plus',
                                         font_size=14,
                                         x=self.window.width // 2, y=6,
                                         anchor_x='center', anchor_y='bottom',
                                         color=arcade.color.BLACK)

        self.dumb_fix_for_logo_pos = False

        self.on_resize(*self.window.size)

        super().setup()

    def calculate_positions(self) -> None:
        self.logo.center_x = self.size[0] // 2
        self.logo.bottom = self.size[1] // 2

        self.press_label.position = (self.window.center_x, self.window.center_y / 2, 0)
        self.welcome_label.position = (self.window.center_x, 6, 0)
        self.splash_label.position = (*self.window.center, 0)

    def generate_splash(self) -> ClownLogo | SplashLogo:
        if self.show_clown:
            # it's tricky
            splash_label = ClownLogo(x=int(self.window.center_x + 100), y=int(self.window.center_y))
        else:
            splashes = pkg_resources.read_text(charm.data, "splashes.txt").splitlines()
            splash_label = SplashLogo(splashes, x=int(self.window.center_x), y=int(self.window.center_y))
        return splash_label

    @shows_errors
    @ignore_imgui
    def on_key_press(self, symbol: int, modifiers: int) -> None:
        super().on_key_press(symbol, modifiers)
        if keymap.start.pressed:
            self.start()
        elif self.window.debug and keymap.log_sync.pressed:
            self.splash_label.next_splash()
        elif self.window.debug and keymap.seek_zero.pressed:
            self.window.theme_song.seek(3)
            self.setup()

    @shows_errors
    @ignore_imgui
    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        if imgui.is_window_hovered(imgui.HOVERED_ANY_WINDOW):
            return
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.start()

    @shows_errors
    def on_update(self, delta_time: float) -> None:
        super().on_update(delta_time)

        move_gum_wrapper(self.logo_width, self.small_logos_forward, self.small_logos_backward, delta_time)

        # Logo bounce
        self.logo.scale = 0.3 + (self.window.beat_animator.factor * 0.025)

        # Splash text typewriter effect
        self.splash_label.on_update(self.local_time)

        self.song_label.on_update(self.local_time)

        self.press_label.on_update(self.local_time, going=self.goto_fade_time is not None and self.goto_switch_time is not None)

        if self.goto_fade_time is not None and self.goto_switch_time is not None:
            if self.local_time >= self.goto_fade_time:
                # Fade music
                VOLUME = 0
                self.window.theme_song.volume = ease_linear(VOLUME, VOLUME / 2, self.goto_fade_time, self.goto_switch_time, self.local_time)
            if self.local_time >= self.goto_switch_time:
                # Go to main menu
                self.goto("mainmenu")

    @shows_errors
    def on_draw(self) -> None:
        self.window.camera.use()
        self.clear()

        if not self.dumb_fix_for_logo_pos:
            # My guess is this is needed because the window size is wrong on the first tick?
            self.calculate_positions()
            self.dumb_fix_for_logo_pos = True

        # Charm BG
        self.small_logos_forward.draw()
        self.small_logos_backward.draw()

        arcade.draw_polygon_filled(
            [(self.welcome_label.x - self.welcome_label._label.content_width // 2, self.welcome_label._label.content_height + 10),
             (self.welcome_label.x - self.welcome_label._label.content_width // 2 + self.welcome_label._label.content_width, self.welcome_label._label.content_height + 10),
             (self.welcome_label.x - self.welcome_label._label.content_width // 2 + self.welcome_label._label.content_width + 20, 0), (self.welcome_label.x - self.welcome_label._label.content_width // 2 - 20, 0)],
            CharmColors.FADED_PURPLE
        )

        self.welcome_label.draw()

        # Logo and text
        self.main_sprites.draw()
        self.splash_label.draw()
        self.song_label.draw()
        self.press_label.draw()

        super().on_draw()

    def start(self) -> None:
        if self.goto_fade_time is not None:
            return
        self.goto_fade_time = self.local_time + FADE_DELAY
        self.goto_switch_time = self.local_time + SWITCH_DELAY
        arcade.play_sound(self.window.sounds["valid"], volume = settings.get_volume("sound"))


class ClownLogo(arcade.Text):
    def __init__(self, x: int, y: int):
        super().__init__(
            "CLOWN KILLS YOU",
            font_name='Impact',
            font_size=48,
            x=x,
            y=y,
            anchor_x='center', anchor_y='top',
            color=arcade.color.RED
        )

    def next_splash(self) -> None:
        return

    def prev_splash(self) -> None:
        return

    def random_splash(self) -> None:
        return

    def jiggle(self) -> None:
        self.rotation = (random.random() * 10) - 5

    def on_update(self, local_time: float) -> None:
        self.jiggle()

class SplashLogo(pyglet.text.Label):
    def __init__(self, splashes: list[str], x: int, y: int):
        self.splashes = splashes
        self.splash_index = 0
        super().__init__(
            font_name='bananaslip plus',
            font_size=24,
            x=x,
            y=y,
            anchor_x='left', anchor_y='top',
            color=CharmColors.PURPLE
        )

    @property
    def splash_text(self) -> str:
        return self.splashes[self.splash_index]

    def next_splash(self) -> None:
        self.splash_index = (self.splash_index + 1) % len(self.splashes)

    def prev_splash(self) -> None:
        self.splash_index = (self.splash_index - 1) % len(self.splashes)

    def random_splash(self) -> None:
        self.splash_index = random.randint(0, len(self.splashes) - 1)

    def on_update(self, local_time: float) -> None:
        self.text = typewriter(self.splash_text, 20, local_time, 3)

class SongLabel(pyglet.text.Label):
    def __init__(self):
        width = 540
        self.x_1 = -width
        self.x_2 = 5
        super().__init__(
            "Run Around The Character Code!\nCamellia feat. nanahira\n3LEEP!",
            width=width,
            font_name='bananaslip plus',
            font_size=16,
            x=self.x_1, y=5,
            anchor_x='left', anchor_y='bottom',
            multiline=True,
            color=CharmColors.PURPLE
        )

    def on_update(self, local_time: float) -> None:
        START_MOVE_RIGHT = 3
        STOP_MOVE_RIGHT = 5
        START_MOVE_LEFT = 8
        STOP_MOVE_LEFT = 10
        # constraining the time when we update the position should decrease lag,
        # even though it's technically unnecessary because the function is clamped
        if START_MOVE_RIGHT <= local_time <= STOP_MOVE_RIGHT:
            self.x = ease_quadinout(self.x_1, self.x_2, START_MOVE_RIGHT, STOP_MOVE_RIGHT, local_time)
        elif START_MOVE_LEFT <= local_time <= STOP_MOVE_LEFT:
            self.x = ease_quadinout(self.x_2, self.x_1, START_MOVE_LEFT, STOP_MOVE_LEFT, local_time)

class PressLabel(pyglet.text.Label):
    def __init__(self, x: int, y: int):
        super().__init__(
            "<press start>",
            font_name='bananaslip plus',
            font_size=32,
            x=x, y=y,
            anchor_x='center', anchor_y='center',
            color=CharmColors.PURPLE
        )
        self.drawme: bool = True

    def on_update(self, local_time: float, going: bool) -> None:
        if going:
            self.drawme = bool(int(local_time) % 2)
        else:
            self.drawme = bool(int(local_time * 8) % 2)

    def draw(self) -> None:
        if self.drawme:
            super().draw()
