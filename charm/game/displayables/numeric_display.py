from __future__ import annotations

from importlib.resources import files, as_file

from arcade import Sprite, SpriteList, Texture,load_texture
import arcade
from arcade.types import Color

import charm.data.images.skins.base as base_skin


class NumericDisplay:
    def __init__(self, x: float, y: float, height: int, inital_digits: int = 7, color: Color = arcade.color.WHITE, show_zeroes = True) -> None:
        self.spritelist = SpriteList()


        path = files(base_skin)
        self.textures: list[Texture] = []
        for n in range(10):
            with as_file(path.joinpath(f"score_{n}.png")) as p:
                self.textures.append(load_texture(p))

        scale = height / self.textures[0].height
        initial_x = x - (self.textures[0].width * scale / 2)
        initial_y = y - (height / 2)

        self.color = color
        self.show_zeroes = show_zeroes

        self._score = 0

        self.digits = [Sprite(self.textures[0], scale = scale, center_x = initial_x - (i * self.textures[0].width * scale), center_y = initial_y) for i in range(inital_digits)]

        for d in self.digits:
            d.color = color

        self.spritelist.extend(self.digits)

        if not self.show_zeroes:
            for d in self.digits:
                d.visible = False
            self.spritelist[0].visible = True

    @property
    def score(self) -> int:
        return self._score

    @score.setter
    def score(self, v: int) -> None:
        if v == self._score:
            return
        self._score = v
        score_str = str(v)[::-1]
        score_len = len(score_str)
        for n, digit in enumerate(self.digits):
            digit.visible = True
            digit.texture = self.textures[0 if n >= score_len else int(score_str[n])]
            if not self.show_zeroes:
                if 10 ** n > v:
                    digit.visible = False

    def draw(self) -> None:
        self.spritelist.draw()
