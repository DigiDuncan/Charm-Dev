from hashlib import sha1
import logging

import arcade
from arcade import Sprite

from charm.lib.anim import ease_circout
from charm.lib.charm import CharmColors
from charm.lib.generic.song import Metadata
from charm.lib.utils import clamp

from charm.ui.utils import get_album_art

logger = logging.getLogger("charm")


class SongMenuItem(Sprite):
    def __init__(self, song: Metadata, w: int = None, h: int = None, *args, **kwargs):
        self.song = song

        self.title = song.title
        self.artist = song.artist
        self.album = song.album

        # Make a real hash, probably on Song.
        self.key = sha1((str(self.title) + str(self.artist) + str(self.album)).encode()).hexdigest()

        window = arcade.get_window()

        self.album_art = get_album_art(self.song)

        self._w = w if w else window.width // 2
        self._h = h if h else window.height // 8

        self._tex = arcade.Texture.create_empty(f"{self.key}-menuitem", (self._w, self._h))
        super().__init__(self._tex, *args, **kwargs)
        arcade.get_window().ctx.default_atlas.add(self._tex)

        self.position = (0, -window.height)

        with arcade.get_window().ctx.default_atlas.render_into(self._tex) as fbo:
            l, b, w, h = fbo.viewport
            temp_cam = arcade.camera.Camera2D(
                viewport=(l, b, w, h),
                projection=(0, w, h, 0),
                position=(0.0, 0.0),
                render_target=fbo
            )
            with temp_cam.activate():
                fbo.clear()
                arcade.draw_circle_filled(self.width - self.height / 2, self.height / 2, self.height / 2, CharmColors.FADED_PURPLE)
                arcade.draw_lrbt_rectangle_filled(0, self.width - self.height / 2, 0, self.height, CharmColors.FADED_PURPLE)
                if (self.artist or self.album):
                    if self.artist:
                        # add the comma
                        artistalbum = self.artist + ", " + str(self.album)
                    else:
                        # only album name
                        artistalbum = self.album
                    arcade.draw_text(
                        self.title, self.width - self.height / 2 - 5, self.height / 2, arcade.color.BLACK,
                        font_size=self.height / 3 * (3 / 4), font_name="bananaslip plus", anchor_x="right"
                    )
                    arcade.draw_text(
                        artistalbum, self.width - self.height / 2 - 5, self.height / 2, arcade.color.BLACK,
                        font_size=self.height / 4 * (3 / 4), font_name="bananaslip plus", anchor_x="right", anchor_y="top"
                    )
                else:
                    arcade.draw_text(
                        self.title, self.width - self.height / 2 - 5, self.height / 2, arcade.color.BLACK,
                        font_size=self.height / 3, font_name="bananaslip plus", anchor_x="right", anchor_y="center"
                    )

        # logger.info(f"Loaded MenuItem {self.title}")


class SongMenu:
    def __init__(self, songs: list[Metadata] = None, radius = 4, buffer = 5, move_speed = 0.2) -> None:
        self._songs = songs
        self.items: list[SongMenuItem] = []
        if songs:
            for song in self._songs:
                self.items.append(SongMenuItem(song))
        # atlas = arcade.TextureAtlas((16384, 16384))
        self.sprite_list = arcade.SpriteList()
        for item in self.items:
            self.sprite_list.append(item)

        self.buffer = buffer
        self.move_speed = move_speed
        self.radius = radius

        self._selected_id = 0

        self.local_time = 0
        self.move_start = 0
        self.old_pos = {}
        for item in self.items:
            self.old_pos[item] = (item.left, item.center_y)

        self.window = arcade.get_window()

    @property
    def selected_id(self) -> int:
        return self._selected_id

    @selected_id.setter
    def selected_id(self, v: int):
        self._selected_id = clamp(0, v, len(self.items) - 1)
        self.move_start = self.local_time
        for item in self.items:
            self.old_pos[item] = (item.left, item.center_y)

    @property
    def selected(self) -> SongMenuItem:
        return self.items[self.selected_id]

    @property
    def move_end(self) -> float:
        return self.move_start + self.move_speed

    def sort(self, key: str, rev: bool = False):
        if self.items:
            selected = self.items[self.selected_id]
            self.items.sort(key=lambda item: item.song.get(key, ""), reverse=rev)
            self.selected_id = self.items.index(selected)

    def update(self, local_time: float):
        self.local_time = local_time
        current = self.items[self.selected_id]
        current.left = ease_circout(self.old_pos[current][0], 0, self.move_start, self.move_end, self.local_time)
        current.center_y = ease_circout(self.old_pos[current][1], self.window.height // 2, self.move_start, self.move_end, self.local_time)
        up_id = self.selected_id
        down_id = self.selected_id
        x_delta = current.width / (self.radius + 1) / 1.5
        x_offset = 0
        y_offset = 0
        for i in range(self.radius * 2 + 1):
            up_id -= 1
            down_id += 1
            x_offset += x_delta
            y_offset += current.height + self.buffer
            if up_id > -1:
                up = self.items[up_id]
                up.left = ease_circout(self.old_pos[up][0], current.left - x_offset, self.move_start, self.move_end, self.local_time)
                up.center_y = ease_circout(self.old_pos[up][1], y_offset + current.center_y, self.move_start, self.move_end, self.local_time)
            if down_id < len(self.items):
                down = self.items[down_id]
                down.left = ease_circout(self.old_pos[down][0], current.left - x_offset, self.move_start, self.move_end, self.local_time)
                down.center_y = ease_circout(self.old_pos[down][1], -y_offset + current.center_y, self.move_start, self.move_end, self.local_time)

    def draw(self):
        self.sprite_list.draw()
