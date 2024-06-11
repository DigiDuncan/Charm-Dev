from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from arcade import BasicSprite

from importlib.resources import files
from functools import cache
import itertools

import PIL.Image
import PIL.ImageDraw
from arcade import Sprite, SpriteList, Texture, color as colors
from arcade.types import Color

import charm.data.images
from charm.lib.utils import img_from_path


class CharmColors:
    GREEN = Color(0x95, 0xdf, 0xaa, 0xff)         # #95dfaa  CHARM_GREEN = Color(158, 223, 170, 255)
    PINK = Color(0xe6, 0x8e, 0xbe, 0xff)          # #e68ebe
    PURPLE = Color(0x9c, 0x84, 0xd9, 0xff)        # #9c84d9
    FADED_GREEN = Color(0xb3, 0xfd, 0xc8, 0xff)   # #b3fdc8
    FADED_PINK = Color(0xff, 0xac, 0xdc, 0xff)    # #ffacdc
    FADED_PURPLE = Color(0xba, 0xa2, 0xf7, 0xff)  # #baa2f7


@cache
def generate_missing_texture_image(w: int, h: int) -> PIL.Image.Image:
    """Generate a classic missing texture of wxh."""
    mt = PIL.Image.new("RGBA", (w, h), colors.BLACK)
    d = PIL.ImageDraw.Draw(mt)
    d.rectangle(((0, 0), (w // 2 - 1, h // 2 - 1)), colors.MAGENTA)  # upper left
    d.rectangle(((w // 2, h // 2), (w, h)), colors.MAGENTA)          # lower right
    return mt


@cache
def load_missing_texture(height: int, width: int) -> Texture:
    image = generate_missing_texture_image(height, width)
    return Texture(image)


class GumWrapper:
    def __init__(self, size: tuple[int, int]):
        """Generate two SpriteLists that makes a gum wrapper-style background."""
        screen_w, screen_h = size
        logo_tex = Texture(img_from_path(files(charm.data.images) / "small-logo.png"))
        tex_w, tex_h = logo_tex.size
        buffer_w, buffer_h = 20, 16
        logo_w, logo_h = tex_w + buffer_w, tex_h + buffer_h
        self.logos_forward = SlidingSpriteList[Sprite](loop_width=logo_w, speed=0.25, alpha=128)
        self.logos_backward = SlidingSpriteList[Sprite](loop_width=logo_w, speed=-0.25, alpha=128)
        spritelists = itertools.cycle([self.logos_forward, self.logos_backward])
        for y in range(0, screen_h + logo_h, logo_h):
            spritelist = next(spritelists)
            for x in range(-logo_w, screen_w + logo_w, logo_w):
                s = Sprite(
                    logo_tex,
                    center_x=x + logo_w / 2,
                    center_y=y + logo_h / 2
                )
                spritelist.append(s)
        self.logos_backward.move(logo_w / 2, 0)

    def on_update(self, delta_time: float) -> None:
        """Move background logos forwards and backwards, looping."""
        self.logos_forward.on_update(delta_time)
        self.logos_backward.on_update(delta_time)

    def draw(self) -> None:
        self.logos_forward.draw()
        self.logos_backward.draw()


class SlidingSpriteList[T: BasicSprite](SpriteList[T]):
    def __init__(self, loop_width: float, speed: float, alpha: int):
        self.loop_width = loop_width
        self.speed = speed  # loops per second
        self.x: float = 0.0
        super().__init__()
        self.alpha = alpha

    def on_update(self, delta_time: float = 1 / 60) -> None:
        """Move background logos forwards and backwards, looping."""
        old_x = self.x
        slide_x = self.loop_width * delta_time * self.speed
        new_x = (old_x + slide_x) % self.loop_width
        self.x = new_x
        to_move = new_x - old_x
        self.move(to_move, 0)
        super().on_update(delta_time)


