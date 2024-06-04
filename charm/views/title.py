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
from charm.lib.anim import ease_linear, ease_quadinout, perc
from charm.lib.charm import CharmColors, GumWrapper
from charm.lib.digiview import DigiView, ignore_imgui, shows_errors
from charm.lib.digiwindow import DigiWindow, Eggs
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
        self.logo: LogoSprite
        self.main_sprites: arcade.SpriteList[arcade.Sprite]
        self.splash_label: SplashLogo | ClownLogo
        self.show_clown: bool = self.window.egg_roll == Eggs.TRICKY
        self.song_label: SongLabel
        self.press_label: PressLabel
        self.goto_fade_time: float | None
        self.goto_switch_time: float | None

    @shows_errors
    def setup(self) -> None:
        self.goto_fade_time = None
        self.goto_switch_time = None

        self.window.theme_song.seek(self.local_time + 3)

        # Generate "gum wrapper" background
        self.gum_wrapper = GumWrapper(self.size)

        arcade.set_background_color(CharmColors.FADED_GREEN)
        self.main_sprites = arcade.SpriteList()

        # Set up main logo
        self.logo = LogoSprite()

        self.main_sprites.append(self.logo)

        self.splash_label = self.generate_splash()
        self.splash_label.random_splash()

        # Song details
        self.song_label = SongLabel()

        # Press start prompt
        self.press_label = PressLabel(x=self.window.width // 2, y=self.window.height // 4)

        self.welcome_label = WelcomeLabel(x=self.window.width // 2, y=6)

        self.on_resize(*self.size)

        super().setup()

    def calculate_positions(self) -> None:
        self.logo.calculate_positions(self.window)
        self.press_label.calculate_positions(self.window)
        self.welcome_label.calculate_positions(self.window)
        self.splash_label.calculate_positions(self.window)

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

        self.gum_wrapper.on_update(delta_time)

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
                self.window.theme_song.volume = ease_linear(VOLUME, VOLUME / 2, perc(self.goto_fade_time, self.goto_switch_time, self.local_time))
            if self.local_time >= self.goto_switch_time:
                # Go to main menu
                self.goto("mainmenu")

    @shows_errors
    def on_draw(self) -> None:
        self.window.camera.use()
        self.clear()

        # Charm BG
        self.gum_wrapper.draw()

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
            x=x, y=y,
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

    def calculate_positions(self, window: DigiWindow) -> None:
        self.position = (*window.center, 0)


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

    def calculate_positions(self, window: DigiWindow) -> None:
        self.position = (*window.center, 0)


class SongLabel(pyglet.text.Label):
    def __init__(self):
        width = 540
        x_left = -width
        x_right = 5
        self.transitions = [
            (3, 5, x_left, x_right),
            (8, 10, x_right, x_left)
        ]
        super().__init__(
            "Run Around The Character Code!\nCamellia feat. nanahira\n3LEEP!",
            width=width,
            font_name='bananaslip plus',
            font_size=16,
            x=x_left, y=5,
            anchor_x='left', anchor_y='bottom',
            multiline=True,
            color=CharmColors.PURPLE
        )

    def on_update(self, local_time: float) -> None:
        # constraining the time when we update the position should decrease lag,
        # even though it's technically unnecessary because the function is clamped
        for start, stop, x_1, x_2 in self.transitions:
            if start <= local_time <= stop:
                p = perc(start, stop, local_time)
                self.x = ease_quadinout(x_1, x_2, p)

    def calculate_positions(self, window: DigiWindow) -> None:
        return


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

    def calculate_positions(self, window: DigiWindow) -> None:
        self.position = (window.center_x, window.center_y / 2, 0)


class WelcomeLabel(arcade.Text):
    def __init__(self, x: int, y: int):
        super().__init__(
            f"welcome, {getpass.getuser()}!",
            font_name='bananaslip plus',
            font_size=14,
            x=x, y=y,
            anchor_x='center', anchor_y='bottom',
            color=arcade.color.BLACK
        )

    def draw(self) -> None:
        content_left = self.x - self.content_width // 2
        arcade.draw_polygon_filled([
            (content_left -  0,                      self.content_height + 10),
            (content_left + self.content_width -  0, self.content_height + 10),
            (content_left + self.content_width + 20, 0),
            (content_left - 20,                      0)
        ], CharmColors.FADED_PURPLE)
        super().draw()

    def calculate_positions(self, window: DigiWindow) -> None:
        self.position = (window.center_x, 6, 0)


class LogoSprite(arcade.Sprite):
    def __init__(self):
        logo_img = img_from_resource(cast(ModuleType, charm.data.images), "logo.png")
        logo_texture = arcade.Texture(logo_img)
        super().__init__(logo_texture)

    def calculate_positions(self, window: DigiWindow) -> None:
        w, h = window.get_size()
        self.center_x = w // 2
        self.bottom = h // 2
