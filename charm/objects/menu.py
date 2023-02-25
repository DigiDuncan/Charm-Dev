import math
import arcade
from arcade import Sprite
from arcade.types import Color
import PIL.Image, PIL.ImageOps  # noqa: E401

import charm.data.icons
from charm.lib.anim import ease_circout
from charm.lib.charm import CharmColors, generate_missing_texture_image
from charm.lib.digiview import DigiView
from charm.lib.settings import Settings
from charm.lib.utils import img_from_resource


class MainMenuItem(Sprite):
    def __init__(self, label: str, icon: str, goto: DigiView,
                 width: int = 200, border_color: Color = arcade.color.WHITE, border_width: int = 0,
                 *args, **kwargs):
        try:
            self.icon = img_from_resource(charm.data.icons, f"{icon}.png")
            self.icon = self.icon.resize((width, width), PIL.Image.LANCZOS)
        except Exception:
            self.icon = generate_missing_texture_image(width, width)
        self.icon = PIL.ImageOps.expand(self.icon, border=border_width, fill=border_color)
        tex = arcade.Texture(f"_icon_{icon}", image=self.icon, hit_box_algorithm=None)
        super().__init__(texture=tex, *args, **kwargs)

        self.goto = goto

        self.label = arcade.Text(label, 0, 0, CharmColors.PURPLE, anchor_x='center', anchor_y="top",
                                 font_name="bananaslip plus", font_size=24)
        self.center_y = Settings.height // 2
        self.jiggle_start = 0


class MainMenu:
    def __init__(self, items: list[MainMenuItem] = []) -> None:
        self.items = items

        self.sprite_list = arcade.SpriteList()
        for item in self.items:
            self.sprite_list.append(item)

        self.loading = False
        self.loading_label = arcade.Text("LOADING...", 0, 0, arcade.color.BLACK, anchor_x='center', anchor_y="bottom",
                                 font_name="bananaslip plus", font_size=24)

        self._selected_id = 0

        self.local_time = 0
        self.move_start = 0
        self.move_speed = 0.3

        self.old_pos = {}
        for item in self.items:
            self.old_pos[item] = (item.center_x, item.scale, item.alpha)

    @property
    def selected_id(self) -> int:
        return self._selected_id

    @selected_id.setter
    def selected_id(self, v: int):
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

    def sort(self, key: str, rev: bool = False):
        selected = self.items[self.selected_id]
        self.items.sort(key=lambda item: getattr(item.song, key), reverse=rev)
        self.selected_id = self.items.index(selected)

    def update(self, local_time: float):
        self.local_time = local_time
        current = self.items[self.selected_id]
        current.center_x = ease_circout(self.old_pos[current][0], Settings.width // 2, self.move_start, self.move_end, self.local_time)
        current.scale = ease_circout(self.old_pos[current][1], 1, self.move_start, self.move_end, self.local_time)
        current.alpha = ease_circout(self.old_pos[current][2], 255, self.move_start, self.move_end, self.local_time)
        current.label.x = current.center_x
        current.label.y = current.bottom
        self.loading_label.x = current.center_x
        self.loading_label.y = current.top

        x_bumper = Settings.width // 4

        for n, item in enumerate(self.items):
            rel_id = n - self.selected_id
            if rel_id == 0:  # current item
                continue
            item.center_x = ease_circout(self.old_pos[item][0], current.center_x + (x_bumper * rel_id), self.move_start, self.move_end, self.local_time)
            item.scale = ease_circout(self.old_pos[item][1], 0.5, self.move_start, self.move_end, self.local_time)
            item.alpha = ease_circout(self.old_pos[item][2], 127, self.move_start, self.move_end, self.local_time)
            item.label.x = item.center_x
            item.label.y = item.bottom

        JIGGLE_TIME = 0.3
        JIGGLES = 5
        if self.selected.jiggle_start != 0 and self.local_time <= self.selected.jiggle_start + JIGGLE_TIME:
            jiggle_amount = 20 * math.sin(self.local_time * ((JIGGLES * 2) / JIGGLE_TIME))
            current.center_x += jiggle_amount

    def draw(self):
        self.sprite_list.draw()

        for i in self.items:
            i.label.draw()

        if self.loading:
            self.loading_label.draw()
