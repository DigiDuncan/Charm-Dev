import importlib.resources as pkg_resources
import math

from arcade import Sprite, SpriteList
from arcade.text import Text
import arcade.color
from pyglet.graphics import Batch

import charm.data.images
from charm.lib.generic.song import Metadata
from charm.lib.utils import clamp

batch = Batch()


class SongLabelWrapper:
    # This is intentionally really hard-coded. If we wanna change anything in this,
    # let's just change it here for now.
    def __init__(self, metadata: Metadata):
        self.metadata = metadata
        self.texts: dict[str, Text] = {}
        self._enabled = True
        self.texts["main"] = Text(self.metadata.title, 50, 0, arcade.color.BLACK, 16, align = "right", anchor_x = "right", anchor_y = "baseline", font_name = "bananaslip plus", batch = batch)
        self.texts["second"] = Text(self.metadata.artist, 50, self.texts["main"].bottom, arcade.color.BLACK, 12, align = "right", anchor_x = "right", anchor_y = "top", font_name = "bananaslip plus", batch = batch)

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, v: bool):
        if v:
            self.enable()
        else:
            self.disable()

    def enable(self):
        for t in self.texts.values():
            t.color.a = 255
            self._enabled = True

    def disable(self):
        for t in self.texts.values():
            t.color.a = 0
            self._enabled = False


class SongMenu:
    def __init__(self, metas: list[Metadata]) -> None:
        self.items: list[Metadata] = metas
        self.items.sort(key = lambda m: m.title)
        self.labels: dict[Metadata, SongLabelWrapper] = {}

        self.window = arcade.get_window()

        self.spritelist = SpriteList()
        for i in range(21):
            with pkg_resources.path(charm.data.images, "menu_card.png") as p:
                self.spritelist.append(Sprite(p, 0.5))

        self.buffer = 5
        self.min_factor = 3.5
        self.max_factor = 1.3
        self.offset = 0.25
        self.in_sin = 0.1666
        self.out_sin = 0.25
        self.shift = -0.125
        self.move_forward = 0.1

        self.y_shift = 0

        self.center_sprite_index = len(self.spritelist) // 2
        center_sprite = self.spritelist[self.center_sprite_index]
        center_sprite.center_y = arcade.get_window().height / 2 + self.y_shift
        for n, s in enumerate(self.spritelist):
            if n == self.center_sprite_index:
                s.right = self.current_y_to_x(s.center_y) + (self.move_forward * arcade.get_window().width)
            else:
                diff = n - self.center_sprite_index
                s.center_y = center_sprite.center_y - (s.height * diff) - (self.buffer * diff) + self.y_shift
                s.right = self.current_y_to_x(s.center_y)

        self.points = [(self.current_y_to_x(i), i) for i in range(-self.window.height, self.window.height * 2)]

    def current_y_to_x(self, y: float) -> float:
        w, h = arcade.get_window().size
        y /= w
        minimum = w / self.min_factor
        maximum = w / self.max_factor
        x = math.sin(y / self.in_sin + self.shift) * self.out_sin + self.offset
        x *= w
        return clamp(minimum, x, maximum)

    def update(self, delta_time: float):
        for n, s in enumerate(self.spritelist):
            if n == self.center_sprite_index:
                s.center_y = arcade.get_window().height / 2 + self.y_shift
                s.right = self.current_y_to_x(s.center_y) + (self.move_forward * arcade.get_window().width)
            else:
                diff = n - self.center_sprite_index
                s.center_y = self.spritelist[self.center_sprite_index].center_y - (s.height * diff) - (self.buffer * diff) + self.y_shift
                s.right = self.current_y_to_x(s.center_y)
        self.points = [(self.current_y_to_x(i), i) for i in range(-self.window.height, self.window.height * 2, 4)]

    def draw(self):
        self.spritelist.draw()
        arcade.draw_line(0, self.window.center_y, self.window.width, self.window.center_y, arcade.color.BLUE, 5)
        arcade.draw_line_strip(self.points, arcade.color.RED, 5)
        batch.draw()
