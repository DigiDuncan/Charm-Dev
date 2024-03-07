from __future__ import annotations

import functools
import logging
import traceback

import arcade
import imgui
from arcade import View

from charm.lib.anim import ease_linear
from charm.lib.charm import generate_gum_wrapper
from charm.lib.digiwindow import DigiWindow
from charm.lib.errors import CharmException, GenericError
from charm.lib.keymap import get_keymap

logger = logging.getLogger("charm")


def shows_errors(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            result = fn(*args, **kwargs)
            return result
        except Exception as e:
            self: DigiView = args[0] if args[0].shown else args[0].back
            if not isinstance(e, CharmException):
                e = GenericError(e)
            self.on_error(e)
            if e._icon == "error":
                logger.error(f"{e.title}: {e.show_message}")
            elif e._icon == "warning":
                logger.warn(f"{e.title}: {e.show_message}")
            elif e._icon == "info":
                logger.info(f"{e.title}: {e.show_message}")
            else:
                logger.info(f"{e.title}: {e.show_message}")  # /shrug
            print(traceback.format_exc())
    return wrapper

def ignore_imgui(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if imgui.is_window_hovered(imgui.HOVERED_ANY_WINDOW):
            return
        result = fn(*args, **kwargs)
        return result
    return wrapper


class DigiView(View):
    def __init__(self, window: DigiWindow = None, *, back: "DigiView" = None,
                 fade_in: float = 0, bg_color = (0, 0, 0)):
        super().__init__(window)
        self.window: DigiWindow = self.window  # This is stupid.
        self.back = back
        self.shown = False
        self.size = self.window.get_size()
        self.local_time = 0.0
        self.fade_in = fade_in
        self.bg_color = bg_color
        self._errors: list[list[CharmException, float]] = []  # [error, seconds to show]

    def on_error(self, error: CharmException):
        offset = len(self._errors) * 4
        error.sprite.center_x += offset
        error.sprite.center_y += offset
        self._errors.append([error, 3])
        arcade.play_sound(self.window.sounds[f"error-{error._icon}"])

    def calculate_positions(self):
        pass

    def setup(self):
        self.local_time = 0

        arcade.set_background_color(self.bg_color)
        self.calculate_positions()

    def on_show(self):
        self.local_time = 0
        self.shown = True

    def on_resize(self, width: int, height: int):
        self.size = (width, height)
        arcade.set_viewport(0, width, 0, height)
        self.window.camera.projection = (0, width, 0, height)
        self.window.camera.set_viewport((0, 0, width, height))

        # Generate "gum wrapper" background
        self.logo_width, self.small_logos_forward, self.small_logos_backward = generate_gum_wrapper(self.size)

        self.calculate_positions()

    def on_key_press(self, symbol: int, modifiers: int):
        keymap = get_keymap()
        if symbol == keymap.debug:
            self.window.debug = not self.window.debug
        elif symbol == keymap.fullscreen:
            self.window.set_fullscreen(not self.window.fullscreen)
        elif symbol == keymap.mute:
            self.window.theme_song.volume = 0
        if self.window.debug and modifiers & arcade.key.MOD_SHIFT:
            match symbol:
                case arcade.key.A:  # show atlas
                    self.window.ctx.default_atlas.save("atlas.png")
        return super().on_key_press(symbol, modifiers)

    def on_update(self, delta_time: float):
        self.local_time += delta_time
        for li in self._errors:
            li[1] -= delta_time
            if li[1] <= 0:
                self._errors.remove(li)

    def on_draw(self):
        if self.local_time <= self.fade_in:
            alpha = ease_linear(255, 0, 0, self.fade_in, self.local_time)
            arcade.draw_lrbt_rectangle_filled(0, self.window.width, 0, self.window.height,
                                             (0, 0, 0, alpha))

        self.window.overlay_draw()

        for (error, _) in self._errors:
            error.sprite.draw()
