import logging

import math
import arcade
from arcade import Sprite, SpriteList

from charm.lib.generic.song import Seconds

logger = logging.getLogger("charm")


class SpriteBucketCollection:
    def __init__(self):
        self.width: Seconds = 5
        self.sprites: list[Sprite] = []
        self.buckets: list[SpriteList[Sprite]] = []
        self.overbucket = SpriteList[Sprite]()
        self.overbucket.program = self.overbucket.ctx.sprite_list_program_no_cull

    def append(self, sprite: Sprite, time: Seconds, length: Seconds) -> None:
        self.sprites.append(sprite)
        b = self.calc_bucket(time)
        b2 = self.calc_bucket(time + length)
        if length != 0:
            logger.info(f"{b}, {b2}")
        if b == b2:
            self.append_bucket(sprite, b)
        else:
            self.overbucket.append(sprite)

    def append_bucket(self, sprite: Sprite, b: int) -> None:
        prog_no_cull = arcade.get_window().ctx.sprite_list_program_no_cull
        while len(self.buckets) <= b:
            s = SpriteList[Sprite]()
            s.program = prog_no_cull
            self.buckets.append(s)
        self.buckets[b].append(sprite)

    def update(self, time: Seconds, delta_time: float = 1 / 60) -> None:
        b = self.calc_bucket(time)
        for bucket in self.buckets[max(b - 2, 0):b + 2]:
            bucket.on_update(delta_time)
        self.overbucket.on_update(delta_time)

    def update_animation(self, time: Seconds, delta_time: float = 1 / 60) -> None:
        b = self.calc_bucket(time)
        for bucket in self.buckets[max(b - 2, 0):b + 2]:
            bucket.update_animation(delta_time)
        self.overbucket.update_animation(delta_time)

    def draw(self, time: Seconds) -> None:
        b = self.calc_bucket(time)
        for bucket in self.buckets[max(b - 2, 0):b + 2]:
            bucket.draw()
        self.overbucket.draw()

    def calc_bucket(self, time: Seconds) -> int:
        return math.floor(time / self.width)
