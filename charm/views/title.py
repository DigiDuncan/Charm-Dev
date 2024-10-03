from __future__ import annotations
from typing import TYPE_CHECKING

from charm.lib.components import Component
from charm.lib.toast import ToastDisplay
if TYPE_CHECKING:
    from charm.lib.digiwindow import DigiWindow

import getpass
from importlib.resources import files
import random

import arcade
from arcade import Text, Sprite, SpriteList, Texture, MOUSE_BUTTON_LEFT, color
from pyglet.text import Label

import charm.data.audio
import charm.data.images
from charm.lib.anim import ease_linear, ease_quadinout, perc
from charm.lib.charm import CharmColors, GumWrapper
from charm.lib.digiview import DigiView, disable_when_focus_lost, shows_errors
from charm.lib.keymap import keymap
from charm.lib.utils import img_from_path, typewriter
from charm.views.mainmenu import MainMenuView
import charm.lib.egg as egg

# -- TEMP --
from arcade.key import KEY_0, KEY_1, KEY_2, KEY_3, KEY_4, KEY_5, KEY_6, KEY_7, KEY_8, KEY_9
key_dict = {
    KEY_0: 0,
    KEY_1: 1,
    KEY_2: 2,
    KEY_3: 3,
    KEY_4: 4,
    KEY_5: 5,
    KEY_6: 6,
    KEY_7: 7,
    KEY_8: 8,
    KEY_9: 9,
}

FADE_DELAY = 1
SWITCH_DELAY = 0.5 + FADE_DELAY


class TitleView(DigiView):
    def __init__(self):
        super().__init__()
        self.splash_label: SplashLogo | ClownLogo
        self.press_label: PressLabel
        self.goto_fade_time: float | None
        self.goto_switch_time: float | None
        self.fade_volume: float | None
        self.components.register(GumWrapper())
        # self.components.register(GumWrapper(size=self.size))  # Old GumWrapper
        # Set up main logo
        self.components.register(LogoSprite(self.window))
        self.splash_label = self.components.register(self.generate_splash())
        # Song details
        self.components.register(SongLabel(self))
        # Press start prompt
        self.press_label = self.components.register(PressLabel(self, x=self.window.width // 2, y=self.window.height // 4))
        self.components.register(WelcomeLabel(x=self.window.width // 2, y=6))

        self.toast = ToastDisplay(width = 480, height = 135)

    @shows_errors
    def setup(self) -> None:
        super().presetup()
        self.goto_fade_time = None
        self.goto_switch_time = None
        self.fade_volume = None
        self.window.theme_song.seek(self.local_time + 3)
        self.splash_label.random_splash()
        keymap.set_controller()
        super().postsetup()

    def generate_splash(self) -> ClownLogo | SplashLogo:
        if egg.state == egg.TRICKY:
            splash_label = ClownLogo(x=int(self.window.center_x + 100), y=int(self.window.center_y))
        else:
            splashes = (files(charm.data) / "splashes.txt").read_text().splitlines()
            splash_label = SplashLogo(self, splashes)
        return splash_label

    @shows_errors
    @disable_when_focus_lost(keyboard=True)
    def on_key_press(self, symbol: int, modifiers: int) -> None:
        super().on_key_press(symbol, modifiers)
        if keymap.start.pressed:
            self.start()
        elif symbol in key_dict:
            con = keymap.bound_controller
            keymap.set_controller(key_dict[symbol])
            if keymap.bound_controller != con:
                self.toast.show_toast("controller", "Controller bound!", f"Controller {key_dict[symbol]} bound to player 1!")
                print(self.toast.local_time, self.toast.last_show_time, self.toast.left)
        elif self.window.debug.enabled and keymap.log_sync.pressed:
            self.splash_label.next_splash()
        elif self.window.debug.enabled and keymap.seek_zero.pressed:
            self.window.theme_song.seek(3)
            self.setup()

    @shows_errors
    @disable_when_focus_lost(mouse=True)
    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        if button == MOUSE_BUTTON_LEFT:
            self.start()

    @shows_errors
    def on_update(self, delta_time: float) -> None:
        super().on_update(delta_time)

        if self.goto_fade_time is not None and self.goto_switch_time is not None and self.fade_volume is not None:
            if self.goto_fade_time <= self.local_time < self.goto_switch_time:
                # Fade music
                self.window.theme_song.volume = ease_linear(self.fade_volume, self.fade_volume / 2, perc(self.goto_fade_time, self.goto_switch_time, self.local_time))
            if self.local_time >= self.goto_switch_time:
                # Go to main menu
                self.go_start()

        self.toast.update(delta_time)

    def on_draw(self) -> None:
        super().on_draw()
        self.toast.draw()

    def start(self) -> None:
        if self.goto_fade_time is not None:
            return
        self.press_label.going = True
        self.goto_fade_time = self.local_time + FADE_DELAY
        self.goto_switch_time = self.local_time + SWITCH_DELAY
        self.sfx.valid.play()
        self.fade_volume = self.window.theme_song.volume

    def go_start(self) -> None:
        v = MainMenuView(back=self)
        v.setup()
        self.goto(v)


class ClownLogo(Text, Component):
    def __init__(self, x: int, y: int):
        super().__init__(
            "CLOWN KILLS YOU",
            font_name='Impact',
            font_size=48,
            x=x, y=y,
            anchor_x='center', anchor_y='top',
            color=color.RED
        )

    def next_splash(self) -> None:
        return

    def prev_splash(self) -> None:
        return

    def random_splash(self) -> None:
        return

    def jiggle(self) -> None:
        self.rotation = (random.random() * 10) - 5

    def on_update(self, delta_time: float) -> None:
        self.jiggle()

    def on_resize(self, width: int, height: int) -> None:
        self.position = (height / 2, width / 2, 0)


class SplashLogo(Label, Component):
    def __init__(self, view: DigiView, splashes: list[str]):
        self.view = view
        self.splashes = splashes
        self.splash_index = 0
        super().__init__(
            font_name='bananaslip plus',
            font_size=24,
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

    def on_update(self, delta_time: float) -> None:
        # Splash text typewriter effect
        self.text = typewriter(self.splash_text, 20, self.view.local_time, 3)

    def on_resize(self, width: int, height: int) -> None:
        self.position = (width // 2, height // 2, 0)


class SongLabel(Label, Component):
    def __init__(self, view: DigiView):
        self.view = view
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

    def on_update(self, delta_time: float) -> None:
        # constraining the time when we update the position should decrease lag,
        # even though it's technically unnecessary because the function is clamped
        for start, stop, x_1, x_2 in self.transitions:
            if start <= self.view.local_time <= stop:
                p = perc(start, stop, self.view.local_time)
                self.x = ease_quadinout(x_1, x_2, p)


class PressLabel(Label, Component):
    def __init__(self, view: DigiView, x: int, y: int):
        self.view = view
        super().__init__(
            "<press start>",
            font_name='bananaslip plus',
            font_size=32,
            x=x, y=y,
            anchor_x='center', anchor_y='center',
            color=CharmColors.PURPLE
        )
        self.drawme: bool = True
        self.going = False

    def on_update(self, delta_time: float) -> None:
        if self.going:
            self.drawme = bool(int(self.view.local_time) % 2)
        else:
            self.drawme = bool(int(self.view.local_time * 8) % 2)

    def draw(self) -> None:
        # Logo and text
        if self.drawme:
            super().draw()

    def on_resize(self, width: int, height: int) -> None:
        self.position = (width / 2, height / 2 / 2, 0)


class WelcomeLabel(Text, Component):
    def __init__(self, x: int, y: int):
        super().__init__(
            f"welcome, {getpass.getuser()}!",
            font_name='bananaslip plus',
            font_size=14,
            x=x, y=y,
            anchor_x='center', anchor_y='bottom',
            color=color.BLACK
        )

    def draw(self) -> None:
        content_left = self.x - self.content_width // 2
        arcade.draw_polygon_filled([
            (content_left - 0,                      self.content_height + 10),
            (content_left + self.content_width - 0, self.content_height + 10),
            (content_left + self.content_width + 20, 0),
            (content_left - 20,                      0)
        ], CharmColors.FADED_PURPLE)
        super().draw()

    def on_resize(self, width: int, height: int) -> None:
        self.position = (width // 2, 6, 0)


# TODO: make a sprite component
class LogoSprite(Sprite, Component):
    def __init__(self, window: DigiWindow):
        self.window = window
        logo_img = img_from_path(files(charm.data.images) / "logo.png")
        logo_texture = Texture(logo_img)
        super().__init__(logo_texture, scale=0.3)
        self.internal_sprite_list: SpriteList[Sprite] = SpriteList()
        self.internal_sprite_list.append(self)

    def on_resize(self, width: int, height: int) -> None:
        self.center_x = width // 2
        self.bottom = height // 2

    def on_update(self, delta_time: float = 1 / 60) -> None:
        self.scale = 0.3 + (self.window.theme_song.beat_factor * 0.025)

    def draw(self) -> None:
        self.internal_sprite_list.draw()



