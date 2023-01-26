import io
import logging
import requests
import os.path

import arcade
from arcade import Sprite
import PIL.Image

from charm.lib.anim import ease_circout
from charm.lib.charm import CharmColors
from charm.lib.generic.song import Metadata
from charm.lib.settings import Settings
from charm.lib.utils import clamp
from charm.lib.paths import songspath

from pathlib import Path

logger = logging.getLogger("charm")


class SongMenuItem(Sprite):
    def __init__(self, song: Metadata, w: int = None, h: int = None, *args, **kwargs):
        self.song = song

        self.title = song.title
        self.artist = song.artist
        self.album = song.album

        # Make a real hash, probably on Song.
        self.key = song.hash

        try:
            album_art_img = PIL.Image.open(f"./albums/album_{self.key}.png")
        except FileNotFoundError:
            art_path = Path(songspath / "fnf" / song.key / "art.jpg") # TODO: check for png as well
            if (not art_path.is_file()):
                album_art = io.BytesIO(requests.get("https://picsum.photos/200.jpg").content)
                album_art_img = PIL.Image.open(album_art)
            else:
                album_art_img = PIL.Image.open(art_path)
            album_art_img = album_art_img.convert("RGBA")
            if (album_art_img.width != 200 or album_art_img.height != 200):
                album_art_img = album_art_img.resize((200, 200))
            album_art_img.save(f"./albums/album_{self.key}.png")
        self.album_art = arcade.Texture(f"{self.key}-albumart", album_art_img, hit_box_algorithm=None)

        self._w = w if w else Settings.width // 2
        self._h = h if h else Settings.height // 8

        self._tex = arcade.Texture.create_empty(f"{self.key}-menuitem", (self._w, self._h))
        super().__init__(texture=self._tex, *args, **kwargs)
        self._sprite_list = arcade.SpriteList()
        self._sprite_list.append(self)

        self.position = (0, -Settings.height)

        with self._sprite_list.atlas.render_into(self._tex) as fbo:
            fbo.clear()
            arcade.draw_circle_filled(self.width - self.height / 2, self.height / 2, self.height / 2, CharmColors.FADED_PURPLE)
            arcade.draw_lrtb_rectangle_filled(0, self.width - self.height / 2, self.height, 0, CharmColors.FADED_PURPLE)
            if (self.artist != "" or self.album != ""):
                if self.artist != "":
                    # add the comma
                    artistalbum = self.artist + ", " + self.album
                else:
                    # only album name
                    artistalbum = self.album
                arcade.draw_text(
                    self.title, self.width - self.height / 2 - 5, self.height / 2, arcade.color.BLACK,
                    font_size=self.height / 3 * (3 / 4), font_name="bananaslip plus plus", anchor_x="right"
                )
                arcade.draw_text(
                    artistalbum, self.width - self.height / 2 - 5, self.height / 2, arcade.color.BLACK,
                    font_size=self.height / 4 * (3 / 4), font_name="bananaslip plus plus", anchor_x="right", anchor_y="top"
                )
            else:
                arcade.draw_text(
                    self.title, self.width - self.height / 2 - 5, self.height / 2, arcade.color.BLACK,
                    font_size=self.height / 3, font_name="bananaslip plus plus", anchor_x="right", anchor_y="center"
                )

        logger.info(f"Loaded MenuItem {self.title}")


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
        selected = self.items[self.selected_id]
        self.items.sort(key=lambda item: item.song.get(key, ""), reverse=rev)
        self.selected_id = self.items.index(selected)

    def update(self, local_time: float):
        self.local_time = local_time
        current = self.items[self.selected_id]
        current.left = ease_circout(self.old_pos[current][0], 0, self.move_start, self.move_end, self.local_time)
        current.center_y = ease_circout(self.old_pos[current][1], Settings.height // 2, self.move_start, self.move_end, self.local_time)
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
