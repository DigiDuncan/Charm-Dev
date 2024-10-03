from importlib.resources import files
import logging
from typing import ClassVar

from arcade import Sprite, SpriteSolidColor, Text, Texture, SpriteList
import arcade
import PIL.Image

import charm.data.images
import charm.data.images.icons
from charm.lib.anim import lerp, perc
from charm.lib.types import Seconds
from charm.lib.utils import get_font_size, img_from_path, px_to_pt

logger = logging.getLogger("charm")

class ToastDisplay:
    _icon_textures: ClassVar[dict[str, Texture]] = {}

    def __init__(self, x: int = None, y: int = None, width: int = 640, height: int = 180, default_on_screen_time: float = 5.0) -> None:
        win = arcade.get_window()
        self.x = x if x is not None else win.width
        self.y = y if y is not None else win.height - 10
        self.width = width
        self.height = height
        self.default_on_screen_time = default_on_screen_time

        self.local_time: Seconds = 0
        self.slide_time: Seconds = 0.25

        self.on_screen_time: float = default_on_screen_time

        self.last_show_time = float('inf')

        self.bg_sprite = Sprite(files(charm.data.images) / "toast.png") # type: ignore - aaaa this DOES work but aaa
        self.bg_sprite.top = self.y
        self.bg_sprite.left = self.x
        self.bg_sprite.width = self.width
        self.bg_sprite.height = self.height
        self.icon: Sprite = SpriteSolidColor(self.height, self.height, color = arcade.color.WHITE)
        self.icon.height = height - 20
        self.icon.width = height - 20
        self.icon.right = self.bg_sprite.right - 10
        self.icon.top = self.bg_sprite.top - 10
        self.main_text: Text = Text("[TOAST]", 0, self.bg_sprite.top, arcade.color.BLACK, px_to_pt(int(self.height / 2)), align = "right", font_name = "bananaslip plus", bold = True, anchor_x = "right", anchor_y = "bottom")
        self.sub_text: Text = Text("[SUBTOAST]", 0, self.main_text.top, arcade.color.BLACK, px_to_pt(int(self.height / 2)), align = "right", font_name = "bananaslip plus", anchor_x = "right", anchor_y = "top")

        self.sprite_list = SpriteList()
        self.sprite_list.append(self.bg_sprite)
        self.sprite_list.append(self.icon)

    def show_toast(self, icon_name: str, main_text: str, sub_text: str, on_screen_time: float | None = None) -> None:
        if icon_name not in self._icon_textures:
            icon_img = img_from_path(files(charm.data.images.icons) / f"{icon_name}.png")
            icon_img = icon_img.resize((self.height - 20, self.height - 20), PIL.Image.LANCZOS)
            ToastDisplay._icon_textures[icon_name] = Texture(icon_img)

        self.icon.texture = self._icon_textures[icon_name]

        self.main_text.text = main_text
        self.sub_text.text = sub_text

        self.main_text.font_size = get_font_size(main_text, px_to_pt(int(self.height / 2)), self.bg_sprite.width - self.icon.width - 50)
        self.sub_text.font_size = get_font_size(sub_text, px_to_pt(int(self.height / 2)), self.main_text.content_width)

        self.main_text.y = self.bg_sprite.center_y
        self.sub_text.y = self.bg_sprite.center_y

        if on_screen_time is None:
            self.on_screen_time = self.default_on_screen_time
        else:
            self.on_screen_time = on_screen_time

        self.last_show_time = self.local_time

    def update(self, delta_time: float) -> None:
        self.local_time += delta_time

    @property
    def left(self) -> float:
        # Early exit
        if self.local_time > self.last_show_time + self.on_screen_time + (self.slide_time * 2):
            return self.x
        elif self.local_time < self.last_show_time:
            return self.x
        # Sliding in
        elif self.local_time < self.last_show_time + self.slide_time:
            p = perc(self.last_show_time, self.last_show_time + self.slide_time, self.local_time)
            return self.x - (self.width * p)
        # Hold time
        elif self.local_time < self.last_show_time + self.on_screen_time + self.slide_time:
            return self.x - self.width
        # Sliding out
        elif self.local_time < self.last_show_time + self.on_screen_time + (self.slide_time * 2):
            p = perc(self.last_show_time + self.on_screen_time + self.slide_time, self.last_show_time + self.on_screen_time + (self.slide_time * 2), self.local_time)
            return self.x - (self.width * (1 - p))
        # ! It shouldn't get to this condition!
        else:
            return self.x

    def draw(self) -> None:
        if self.local_time > self.last_show_time + self.on_screen_time + (self.slide_time * 2):
            return
        elif self.local_time < self.last_show_time:
            return

        self.bg_sprite.left = self.left
        self.icon.right = self.bg_sprite.right
        self.main_text.x = self.icon.left
        self.sub_text.x = self.icon.left

        self.sprite_list.draw()
        self.main_text.draw()
        self.sub_text.draw()
