import getpass
import importlib.resources as pkg_resources
import random
from types import ModuleType
from typing import cast

import arcade
import imgui

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
        super().__init__(bg_color=CharmColors.FADED_GREEN)
        self.logo = None
        self.song = None
        self.sounds: dict[str, arcade.Sound] = {}
        self.main_menu_view = MainMenuView(back=self)
        self.window.theme_song.seek(self.local_time + 3)

        self.dumb_fix_for_logo_pos = False

    def calculate_positions(self) -> None:
        self.logo.center_x = self.size[0] // 2
        self.logo.bottom = self.size[1] // 2

        self.press_label.position = (self.window.center_x, self.window.center_y / 2, 0)
        self.welcome_label.position = (self.window.center_x, 6, 0)
        self.splash_label.position = (*self.window.center, 0)

    @shows_errors
    def setup(self) -> None:
        self.hit_start = None
        self.local_time = 0

        arcade.set_background_color(CharmColors.FADED_GREEN)
        self.main_sprites = arcade.SpriteList()

        # Set up main logo
        logo_img = img_from_resource(cast(ModuleType, charm.data.images), "logo.png")
        logo_texture = arcade.Texture(logo_img)
        self.logo = arcade.Sprite(logo_texture)

        self.main_sprites.append(self.logo)

        self.splashes = pkg_resources.read_text(charm.data, "splashes.txt").splitlines()
        self.splash_text = ""
        self.splash_index = 0
        self.generate_splash()

        # Song details
        self.song_label = arcade.pyglet.text.Label("Run Around The Character Code!\nCamellia feat. nanahira\n3LEEP!",
                                                   width=540,
                                                   font_name='bananaslip plus',
                                                   font_size=16,
                                                   x=5, y=5,
                                                   anchor_x='left', anchor_y='bottom',
                                                   multiline=True,
                                                   color=CharmColors.PURPLE)
        self.song_label.original_x = self.song_label.x
        self.song_label.x = -self.song_label.width

        # Press start prompt
        self.press_label = arcade.pyglet.text.Label("<press start>",
                                                    font_name='bananaslip plus',
                                                    font_size=32,
                                                    x=self.window.width // 2, y=self.window.height // 4,
                                                    anchor_x='center', anchor_y='center',
                                                    color=CharmColors.PURPLE)

        self.welcome_label = arcade.Text(f"welcome, {getpass.getuser()}!",
                                         font_name='bananaslip plus',
                                         font_size=14,
                                         x=self.window.width // 2, y=6,
                                         anchor_x='center', anchor_y='bottom',
                                         color=arcade.color.BLACK)

        self.dumb_fix_for_logo_pos = False

        self.on_resize(*self.window.size)

        super().setup()

    def generate_splash(self) -> None:
        if self.window.egg_roll == Eggs.TRICKY:
            # it's tricky
            self.splash_text = ""
            self.splash_label = arcade.Text("CLOWN KILLS YOU",
                                            font_name='Impact',
                                            font_size=48,
                                            x=self.window.center_x + 100,
                                            y=self.window.center_y,
                                            anchor_x='center', anchor_y='top',
                                            color=arcade.color.RED)
        else:
            self.splash_text = random.choice(self.splashes)
            self.splash_index = self.splashes.index(self.splash_text)
            self.splash_label = arcade.pyglet.text.Label(self.splash_text,
                                                         font_name='bananaslip plus',
                                                         font_size=24,
                                                         x=self.window.center_x,
                                                         y=self.window.center_y,
                                                         anchor_x='left', anchor_y='top',
                                                         color=CharmColors.PURPLE)

    @shows_errors
    @ignore_imgui
    def on_key_press(self, symbol: int, modifiers: int) -> None:
        super().on_key_press(symbol, modifiers)
        if keymap.start.pressed:
            self.hit_start = self.local_time
            arcade.play_sound(self.window.sounds["valid"], volume = settings.get_volume("sound"))
        elif self.window.debug and keymap.log_sync.pressed:
            self.splash_index += 1
            self.splash_index %= len(self.splashes)
            self.splash_text = self.splashes[self.splash_index]
        elif self.window.debug and keymap.seek_zero.pressed:
            self.window.theme_song.seek(3)
            self.setup()

    @shows_errors
    @ignore_imgui
    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        if imgui.is_window_hovered(imgui.HOVERED_ANY_WINDOW):
            return
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.hit_start = self.local_time
            arcade.play_sound(self.window.sounds["valid"])

    @shows_errors
    def on_update(self, delta_time) -> None:
        super().on_update(delta_time)

        move_gum_wrapper(self.logo_width, self.small_logos_forward, self.small_logos_backward, delta_time)

        # Logo bounce
        self.logo.scale = 0.3 + (self.window.beat_animator.factor * 0.025)

        # Splash text typewriter effect
        if self.window.egg_roll == Eggs.TRICKY:
            self.splash_label.rotation = (random.random() * 10) - 5
        else:
            self.splash_label.rotation = 0
            self.splash_label.text = typewriter(self.splash_text, 20, self.local_time, 3)

        # Song name in and out
        if 3 <= self.local_time <= 5:  # constraining the time when we update the position should decrease lag,
                                       # even though it's technically unnecessary because the function is clamped
            self.song_label.x = ease_quadinout(-self.song_label.width, self.song_label.original_x, 3, 5, self.local_time)
        elif 8 <= self.local_time <= 10:
            self.song_label.x = ease_quadinout(self.song_label.original_x, -self.song_label.width, 8, 10, self.local_time)

        if self.hit_start is not None:
            # Fade music
            if self.local_time >= self.hit_start + FADE_DELAY:
                VOLUME = 0
                self.window.theme_song.volume = ease_linear(VOLUME, VOLUME / 2, self.hit_start + FADE_DELAY, self.hit_start + SWITCH_DELAY, self.local_time)
            # Go to main menu
            if self.local_time >= self.hit_start + SWITCH_DELAY:
                self.main_menu_view.setup()
                self.window.show_view(self.main_menu_view)

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
        if self.hit_start is None:
            if int(self.local_time) % 2:
                self.press_label.draw()
        else:
            if int(self.local_time * 8) % 2:
                self.press_label.draw()

        super().on_draw()
