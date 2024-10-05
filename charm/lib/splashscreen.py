from importlib.resources import files
from typing import NamedTuple
from collections.abc import Generator
from math import sin, pi

from arcade import Sprite, Texture
import arcade

from charm.lib.digiview import DigiView
from charm.lib.utils import img_from_path
import charm.data.images


class Splash(NamedTuple):
    src: str
    scale: float
    duration: float
    is_growing: bool
    is_pixelated: bool = False
    do_fade_in: bool = True
    do_fade_out: bool = True


SPLASHES: tuple[Splash, ...] = (Splash("alpha.png", 1280 / 1920, 5.0, False), )


class SplashView(DigiView):

    def __init__(self, next_view: type):
        super().__init__()
        self._next = next_view()

        self._splash_sprite: Sprite | None = None
        self._splash_timer: float = 0.0
        self._current_splash: Splash | None = None
        self._splashes: Generator[Splash] = (splash for splash in SPLASHES)

    def leave(self) -> None:
        self._splash_sprite = None
        self._next.setup()
        self.window.show_view(self._next)

    def _next_splash(self) -> None:
        self._current_splash = next(self._splashes, None)

        if self._current_splash is None or self._splash_sprite is None:
            self.leave()
            return

        self._splash_timer = 0.0

        self._splash_sprite.scale = self._current_splash.scale
        self._splash_sprite.texture = Texture(img_from_path(files(charm.data.images) / self._current_splash.src)) # type: ignore | this is some image bs
        self._splash_sprite.scale = self._current_splash.scale
        self._splash_sprite.alpha = 255 * (not self._current_splash.do_fade_in)

    def on_show_view(self) -> None:
        super().on_show_view()
        self._splash_sprite = Sprite()
        self._next_splash()

    def on_key_release(self, symbol: int, modifiers: int) -> None:
        self._current_splash = None
        self.leave()

    def on_update(self, delta_time: float) -> None:
        if self._current_splash is None:
            return

        self._splash_timer += delta_time

        if self._splash_timer >= self._current_splash.duration:
            self._next_splash()
            return

        if not self._splash_sprite:
            return

        self._splash_sprite.position = self.window.center

        splash_fraction = self._splash_timer / self._current_splash.duration

        if self._current_splash.is_growing:
            self._splash_sprite.scale = self._current_splash.scale + splash_fraction * 0.25

        fade_fraction = min(0.5 + 0.5 * self._current_splash.do_fade_out, max(0.5 - 0.5 * self._current_splash.do_fade_in, splash_fraction))
        self._splash_sprite.alpha = int(255 * sin(pi * fade_fraction))

    def on_draw(self) -> None:
        self.clear()

        if self._current_splash is None or self._splash_sprite is None:
            return

        arcade.draw_sprite(self._splash_sprite, pixelated=self._current_splash.is_pixelated)
