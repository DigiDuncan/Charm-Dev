import importlib.resources as pkg_resources
import logging
from math import ceil
import math
from typing import Literal

import arcade
from arcade import Sprite, SpriteList, Texture

from charm.lib.anim import EasingFunction, ease_linear, ease_quadinout
from charm.lib.charm import CharmColors, generate_gum_wrapper, load_missing_texture, move_gum_wrapper
from charm.lib.digiview import DigiView, shows_errors, ignore_imgui
from charm.lib.types import Point, Seconds, TuplePoint
import charm.data.images
from charm.lib.utils import clamp


logger = logging.getLogger("charm")


class XShifter:
    def __init__(self, min_factor: float, max_factor: float, offset: float,
                 in_sin: float, out_sin: float, shift: float = 0.0,
                 move_forward: float = 0.0, y_shift: float = 0.0) -> None:
        self.min_factor = min_factor
        self.max_factor = max_factor
        self.offset = offset
        self.in_sin = in_sin
        self.out_sin = out_sin
        self.shift = shift
        self.move_forward = move_forward
        self.y_shift = y_shift

    def current_y_to_x(self, y: float, w = None) -> float:
        y += self.y_shift
        w = w if w is not None else arcade.get_window().width
        y /= w
        minimum = w / self.min_factor
        maximum = w / self.max_factor
        x = math.sin(y / self.in_sin + self.shift) * self.out_sin + self.offset
        x *= w
        return clamp(minimum, x, maximum) + (self.move_forward * w)


class SpriteCycler:
    def __init__(self, texture: Texture, easing_function: EasingFunction = ease_linear,
                 height = None, shift_time: Seconds = 0.25, position: TuplePoint = (0, 0),
                 buffer = 0, sprite_scale = 1):
        self.easing_function = easing_function
        self.height = arcade.get_window().height if height is None else height
        self.shift_time = shift_time
        self.position = Point(position)
        self.buffer = buffer

        self.texture_height = texture.height * sprite_scale
        sprites = [Sprite(texture, sprite_scale) for i in range(ceil(self.height / self.texture_height) + 10)]

        self.sprite_list: SpriteList[Sprite] = SpriteList()
        self.sprite_list.extend(sprites)

        self._sprite_count = len(self.sprite_list)

        self._animation_progress: float = 0
        self._animating: Literal[-1, 0, 1] = 0

        self.x_shifter = XShifter(3.5, 1.3, 0.25, 0.1666, 0.25, -0.125, 0.1)

        self.MAX_SCROLL_SPEED = 10  # per s
        self.last_scroll_event = 0

        self.layout()

    @property
    def animation_over(self) -> bool:
        return self._animation_progress > self.shift_time or self._animation_progress < -self.shift_time

    @property
    def animation_offset(self) -> float:
        norm = abs(self._animation_progress / self.shift_time)
        return self.easing_function(0, self.texture_height, 0, 1, norm) * self._animating

    def layout(self):
        top_y = self.height + ((self.texture_height + self.buffer) * 5) + self.animation_offset
        for n, sprite in enumerate(self.sprite_list):
            sprite.top = top_y - ((self.buffer + self.texture_height) * n)
            sprite.left = self.position.x + self.x_shifter.current_y_to_x(sprite.center_y)

    def shift(self, up = False):
        self._animation_progress = 0
        self._animating = -1 if not up else 1

    def mouse_scroll(self, time: float, up = False):
        if time > (self.last_scroll_event + (1 / self.MAX_SCROLL_SPEED)):
            self.shift(up)
            self.last_scroll_event = time

    def update(self, delta_time: float):
        if self._animating:
            self._animation_progress += (delta_time * self._animating)
            self.layout()
        if self.animation_over:
            self._animating = 0
            self._animation_progress = 0
            self.layout()

    def draw(self):
        self.sprite_list.draw()


class CycleView(DigiView):
    def __init__(self, *args, **kwargs):
        super().__init__(fade_in=1, bg_color=CharmColors.FADED_GREEN, *args, **kwargs)
        self.volume = 1
        self.cycler = SpriteCycler(load_missing_texture(100, 100))

    @shows_errors
    def setup(self):
        super().setup()

        with pkg_resources.path(charm.data.images, "menu_card.png") as p:
            tex = arcade.load_texture(p)

        x = -(arcade.get_window().height * 1.5)
        self.cycler = SpriteCycler(tex, easing_function = ease_quadinout,
                                   shift_time = 0.25, sprite_scale = 0.4, position = (x, 0))

        # Generate "gum wrapper" background
        self.logo_width, self.small_logos_forward, self.small_logos_backward = generate_gum_wrapper(self.size)

    def on_show_view(self):
        self.window.theme_song.volume = 0

    @shows_errors
    @ignore_imgui
    def on_key_press(self, symbol: int, modifiers: int):
        match symbol:
            case arcade.key.BACKSPACE:
                self.back.setup()
                self.window.show_view(self.back)
                arcade.play_sound(self.window.sounds["back"])
            case arcade.key.UP:
                self.cycler.shift(True)
                arcade.play_sound(self.window.sounds["select"])
            case arcade.key.DOWN:
                self.cycler.shift(False)
                arcade.play_sound(self.window.sounds["select"])

        return super().on_key_press(symbol, modifiers)

    def calculate_positions(self):
        x = -(arcade.get_window().height * 1.5)
        self.cycler.position = Point((x, 0))
        self.cycler.layout()
        super().calculate_positions()

    @shows_errors
    @ignore_imgui
    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        if scroll_y == 0:
            return
        elif scroll_y > 0:
            self.cycler.mouse_scroll(self.local_time, True)
        else:
            self.cycler.mouse_scroll(self.local_time, False)
        arcade.play_sound(self.window.sounds["select"])

    @shows_errors
    def on_update(self, delta_time):
        super().on_update(delta_time)
        self.cycler.update(delta_time)

        move_gum_wrapper(self.logo_width, self.small_logos_forward, self.small_logos_backward, delta_time)

    @shows_errors
    def on_draw(self):
        self.window.camera.use()
        self.clear()

        # Charm BG
        self.small_logos_forward.draw()
        self.small_logos_backward.draw()

        self.cycler.draw()
        super().on_draw()
