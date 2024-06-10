from __future__ import annotations
from typing import TYPE_CHECKING, cast
from types import ModuleType
if TYPE_CHECKING:
    from charm.lib.digiwindow import DigiWindow
    from charm.lib.digiview import DigiView

import math

import PIL.Image, PIL.ImageOps  # noqa: E401
import arcade
from arcade import Sprite
from arcade.types import Color

import charm.data.icons
from charm.lib.anim import ease_circout, perc
from charm.lib.charm import CharmColors, generate_missing_texture_image
from charm.lib.utils import img_from_resource


def load_icon_texture(icon: str, width: int, border_width: int, border_color: Color) -> arcade.Texture:
    try:
        image = img_from_resource(cast(ModuleType, charm.data.icons), f"{icon}.png").resize((width, width), PIL.Image.LANCZOS)
    except Exception:
        image = generate_missing_texture_image(width, width)
    image_expanded = PIL.ImageOps.expand(image, border=border_width, fill=border_color)
    tex = arcade.Texture(image_expanded)
    return tex


class MainMenuItem(Sprite):
    def __init__(
        self,
        label: str,
        icon: str,
        goto: DigiView | None,
        width: int = 200,
        border_color: Color = arcade.color.WHITE,
        border_width: int = 0
    ):
        tex = load_icon_texture(icon, width, border_width, border_color)
        super().__init__(tex)

        self.goto = goto

        self.label = arcade.Text(
            label,
            0, 0,
            CharmColors.PURPLE if self.goto is not None else arcade.color.GRAY,
            anchor_x="center",
            anchor_y="top",
            font_name="bananaslip plus",
            font_size=24
        )
        self.center_y = arcade.get_window().height // 2
        self.jiggle_start: float = 0
        self.window: DigiWindow = arcade.get_window() # type: ignore

    def start_jiggle(self) -> None:
        self.jiggle_start = self.window.time

    def go(self) -> bool:
        if self.goto is None:
            return False
        self.goto.setup()
        self.window.show_view(self.goto)
        self.window.sfx.valid.play()
        return True


class MainMenu:
    def __init__(self, items: list[MainMenuItem]) -> None:
        self.items = items
        self.window: DigiWindow = arcade.get_window() # type: ignore

        self.sprite_list = arcade.SpriteList[MainMenuItem]()
        for item in self.items:
            self.sprite_list.append(item)

        self.loading = False
        self.loading_label = arcade.Text("LOADING...", 0, 0, arcade.color.BLACK, anchor_x='center', anchor_y="bottom",
                                         font_name="bananaslip plus", font_size=24)

        self._selected_id = 0

        self.move_start = 0
        self.move_speed = 0.3

        self.old_pos: dict[MainMenuItem, tuple[float, float, int]] = {}
        for item in self.items:
            self.old_pos[item] = (item.center_x, item.scale, item.alpha)

    @property
    def local_time(self) -> float:
        return self.window.time

    def recreate(self) -> None:
        old_id = self._selected_id
        self = self.__class__(self.items)
        self._selected_id = old_id
        for i in self.items:
            i.center_y = arcade.get_window().height // 2

    @property
    def selected_id(self) -> int:
        return self._selected_id

    @selected_id.setter
    def selected_id(self, v: int) -> None:
        self._selected_id = v % len(self.items)
        self.move_start = self.local_time
        for item in self.items:
            self.old_pos[item] = (item.center_x, item.scale, item.alpha)

    @property
    def selected(self) -> MainMenuItem:
        return self.items[self.selected_id]

    @property
    def move_end(self) -> float:
        return self.move_start + self.move_speed

    def get_item_at(self, x: float, y: float) -> MainMenuItem | None:
        for item in self.items:
            if item.collides_with_point((x, y)):
                return item
        return None

    def on_update(self, delta_time: float) -> None:
        current = self.selected
        current.center_x = ease_circout(self.old_pos[current][0], self.window.width // 2, perc(self.move_start, self.move_end, self.local_time))
        current.scale = ease_circout(self.old_pos[current][1], 1, perc(self.move_start, self.move_end, self.local_time))
        current.alpha = int(ease_circout(self.old_pos[current][2], 255, perc(self.move_start, self.move_end, self.local_time)))
        current.label.x = current.center_x
        current.label.y = current.bottom
        self.loading_label.x = current.center_x
        self.loading_label.y = current.top

        x_bumper = self.window.width // 4

        for n, item in enumerate(self.items):
            if self.selected_id == n:  # current item
                continue
            rel_id = n - self.selected_id
            item.center_x = ease_circout(self.old_pos[item][0], current.center_x + (x_bumper * rel_id), perc(self.move_start, self.move_end, self.local_time))
            item.scale = ease_circout(self.old_pos[item][1], 0.5, perc(self.move_start, self.move_end, self.local_time))
            item.alpha = int(ease_circout(self.old_pos[item][2], 127, perc(self.move_start, self.move_end, self.local_time)))
            item.label.x = item.center_x
            item.label.y = item.bottom

        JIGGLE_TIME = 0.3
        JIGGLES = 5
        if self.selected.jiggle_start != 0 and self.window.time <= self.selected.jiggle_start + JIGGLE_TIME:
            jiggle_amount = 20 * math.sin(self.window.time * ((JIGGLES * 2) / JIGGLE_TIME))
            current.center_x += jiggle_amount

    def draw(self) -> None:
        self.sprite_list.draw()

        for i in self.items:
            i.label.draw()

        if self.loading:
            self.loading_label.draw()
