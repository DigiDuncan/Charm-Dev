import importlib.resources as pkg_resources
import math

from arcade import Sprite, SpriteList
from arcade.text import Text
import arcade.color
from pyglet.graphics import Batch

import charm.data.images
from charm.lib.generic.song import Metadata

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

        self.spritelist = SpriteList()
        for i in range(20):
            with pkg_resources.path(charm.data.images, "menu_card.png") as p:
                self.spritelist.append(Sprite(p, 0.5))

        for n, s in enumerate(self.spritelist):
            if n == 0:
                s.bottom = 5
            else:
                s.bottom = self.spritelist[n - 1].top + 5
            w, h = arcade.get_window().size
            p = 0.75
            s.right = max(p, math.cos(s.center_y / (h / (math.pi / 2)) - 0.8)) * (w / 1.75)

    def draw(self):
        self.spritelist.draw()
        batch.draw()
