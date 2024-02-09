import math
import arcade

from charm.lib.generic.song import Seconds


class SpriteBucketCollection:
    def __init__(self):
        self.width: Seconds = 5
        self.sprites: list[arcade.Sprite] = []
        self.buckets: list[arcade.SpriteList] = []
        self.overbucket = arcade.SpriteList()

    def append(self, sprite: arcade.Sprite, time: Seconds, length: Seconds):
        self.sprites.append(sprite)
        b = self.calc_bucket(time)
        b2 = self.calc_bucket(time + length)
        if b == b2:
            self.append_bucket(sprite, b)
        else:
            self.overbucket.append(sprite)

    def append_bucket(self, sprite, b):
        while len(self.buckets) <= b:
            self.buckets.append(arcade.SpriteList())
        self.buckets[b].append(sprite)

    def update(self, time: Seconds, delta_time: float = 1 / 60):
        b = self.calc_bucket(time)
        for bucket in self.buckets[max(b - 2, 0):b + 2]:
            bucket.update(delta_time)
        self.overbucket.update(delta_time)

    def update_animation(self, time: Seconds, delta_time: float = 1 / 60):
        b = self.calc_bucket(time)
        for bucket in self.buckets[max(b - 2, 0):b + 2]:
            bucket.update_animation(delta_time)
        self.overbucket.update_animation(delta_time)

    def draw(self, time: Seconds):
        b = self.calc_bucket(time)
        for bucket in self.buckets[max(b - 2, 0):b + 2]:
            bucket.draw()
        self.overbucket.draw()

    def calc_bucket(self, time: Seconds) -> int:
        return math.floor(time / self.width)
