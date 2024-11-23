from arcade import Sprite, SpriteCircle, draw_rect_filled, draw_sprite, LRBT
from arcade.types import Color
from arcade.color import BLACK

from charm.game.generic import BaseEngine
from charm.core.charm import CharmColors
from charm.lib.utils import map_range
from charm.lib.anim import lerp

class HPBar:
    def __init__(self, x: float, y: float,
                 height: float, width: float,
                 engine: BaseEngine,
                 color: Color = BLACK,
                 center_sprite: Sprite | None = None):
        self.x = x
        self.y = y
        self.height = height
        self.width = width
        self.color = color
        self.engine = engine
        self.center_sprite: Sprite = center_sprite if center_sprite else SpriteCircle(int(self.height * 2), CharmColors.PURPLE)

        self.center_sprite.center_x = x
        self.center_sprite.center_y = y

    def update(self, song_time: float) -> None:
        pass

    def draw(self) -> None:
        hp_min = self.x - self.width // 2
        hp_max = self.x + self.width // 2
        hp_normalized = map_range(self.engine.hp, self.engine.min_hp, self.engine.max_hp, 0, 1)
        hp = lerp(hp_min, hp_max, hp_normalized)
        draw_rect_filled(LRBT(
            hp_min, hp_max,
            self.y - self.height // 2, self.y + self.height // 2),
            self.color
        )
        self.center_sprite.center_x = hp
        draw_sprite(self.center_sprite)