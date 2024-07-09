from __future__ import annotations

from typing import TYPE_CHECKING

from arcade import Sprite, SpriteCircle, draw_lrbt_rectangle_filled
import arcade
from arcade.types import Point, Color

from charm.lib.anim import lerp
from charm.lib.charm import CharmColors
from charm.lib.utils import map_range

if TYPE_CHECKING:
    from charm.lib.digiwindow import DigiWindow
    from charm.lib.generic.engine import Engine
    from charm.lib.generic.song import Chart
    from charm.lib.generic.sprite import NoteSprite
    from charm.lib.types import Seconds


class HPBar:
    def __init__(self, x: float, y: float,
                 height: float, width: float,
                 engine: Engine,
                 color: Color = arcade.color.BLACK,
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

    def draw(self) -> None:
        hp_min = self.x - self.width // 2
        hp_max = self.x + self.width // 2
        hp_normalized = map_range(self.engine.hp, self.engine.min_hp, self.engine.max_hp, 0, 1)
        hp = lerp(hp_min, hp_max, hp_normalized)
        arcade.draw_lrbt_rectangle_filled(
            hp_min, hp_max,
            self.y - self.height // 2, self.y + self.height // 2,
            self.color
        )
        self.center_sprite.center_x = hp
        arcade.draw_sprite(self.center_sprite)


class Display[ET: Engine, CT: Chart]:

    def __init__(self, window: DigiWindow, engine: ET, charts: tuple[CT, ...]):
        self._win: DigiWindow = window
        self._engine: ET = engine
        self._charts: tuple[CT, ...] = charts

    def update(self, song_time: Seconds) -> None:
        pass

    def draw(self) -> None:
        pass

    def pause(self) -> None:
        pass

    def unpause(self) -> None:
        pass

    # -- DEBUG METHODS --

    def debug_fetch_note_sprites_at_point(self, point: Point) -> list[NoteSprite]:
        ...
