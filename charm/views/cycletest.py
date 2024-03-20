import importlib.resources as pkg_resources
import logging
from math import ceil
from typing import Literal

import arcade
from arcade import Sprite, SpriteList, Texture

from charm.lib.anim import EasingFunction, ease_linear, ease_quadinout
from charm.lib.charm import CharmColors, generate_gum_wrapper, move_gum_wrapper
from charm.lib.digiview import DigiView, shows_errors, ignore_imgui
from charm.lib.types import Point, Seconds, TuplePoint
import charm.data.images


logger = logging.getLogger("charm")


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
            sprite.left = self.position.x

    def shift(self, up = False):
        self._animation_progress = 0
        self._animating = -1 if not up else 1

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

    @shows_errors
    def setup(self):
        super().setup()

        with pkg_resources.path(charm.data.images, "menu_card.png") as p:
            tex = arcade.load_texture(p)

        self.cycler = SpriteCycler(tex, easing_function = ease_quadinout,
                                   shift_time = 0.25, sprite_scale = 0.4)

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
            case arcade.key.DOWN:
                self.cycler.shift(False)

        return super().on_key_press(symbol, modifiers)

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
