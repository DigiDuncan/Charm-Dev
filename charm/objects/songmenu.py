from collections.abc import Iterable
from hashlib import sha1
import logging
from operator import attrgetter
from typing import cast

import arcade
from arcade import LBWH, LRBT, Sprite, SpriteList, Texture, Camera2D, color as colors

from charm.lib.anim import ease_circout, perc
from charm.lib.charm import CharmColors
from charm.lib.errors import NoSongsFoundError
from charm.lib.generic.song import Metadata
from charm.lib.utils import clamp

from charm.lib.utils import get_album_art

logger = logging.getLogger("charm")


class SongMenuItem(Sprite):
    def __init__(self, song: Metadata):
        self.song = song

        self.title = song.title
        self.artist = song.artist
        self.album = song.album

        self.album_art = get_album_art(self.song)


        window = arcade.get_window()

        # Make a real hash, probably on Song.
        key = sha1((str(self.title) + str(self.artist) + str(self.album)).encode()).hexdigest()
        size = (
            window.width // 2,
            window.height // 8
        )
        _tex = Texture.create_empty(f"{key}-menuitem", size)
        super().__init__(_tex)
        window.ctx.default_atlas.add(_tex)

        self.position = (0, -window.height)

        with window.ctx.default_atlas.render_into(_tex) as fbo:
            l, b, w, h = cast("tuple[int, int, int, int]", fbo.viewport)
            temp_cam = Camera2D(
                viewport=LBWH(l, b, w, h),
                projection=LRBT(0, w, h, 0),
                position=(0.0, 0.0),
                render_target=fbo
            )
            with temp_cam.activate():
                fbo.clear()
                arcade.draw_circle_filled(self.width - self.height / 2, self.height / 2, self.height / 2, CharmColors.FADED_PURPLE)
                arcade.draw_lrbt_rectangle_filled(0, self.width - self.height / 2, 0, self.height, CharmColors.FADED_PURPLE)
                if (self.artist or self.album):
                    if self.artist:
                        # Has artist
                        # add the comma
                        artistalbum = self.artist + ", " + str(self.album)
                    else:
                        # No artist but has Album
                        # only album name
                        artistalbum = self.album
                    # Has artist OR album
                    arcade.draw_text(
                        self.title,
                        int(self.width - self.height / 2 - 5),
                        int(self.height / 2),
                        colors.BLACK,
                        font_size=self.height / 3 * (3 / 4),
                        font_name="bananaslip plus",
                        anchor_x="right"
                    )
                    arcade.draw_text(
                        artistalbum,
                        int(self.width - self.height / 2 - 5),
                        int(self.height / 2),
                        colors.BLACK,
                        font_size=self.height / 4 * (3 / 4),
                        font_name="bananaslip plus",
                        anchor_x="right",
                        anchor_y="top"
                    )
                else:
                    # No artist & No album
                    arcade.draw_text(
                        self.title,
                        int(self.width - self.height / 2 - 5),
                        int(self.height / 2),
                        colors.BLACK,
                        font_size=self.height / 3,
                        font_name="bananaslip plus",
                        anchor_x="right",
                        anchor_y="center"
                    )


class SongMenu:
    def __init__(self, songs: Iterable[Metadata] = (), radius: int = 4, buffer: int = 5, move_speed: float = 0.2) -> None:
        self.items = [SongMenuItem(song) for song in songs]
        if len(self.items) == 0:
            raise NoSongsFoundError
        self.sprite_list = SpriteList[SongMenuItem]()
        self.sprite_list.extend(self.items)

        self.buffer = buffer
        self.move_speed = move_speed
        self.radius = radius

        self._selected_id = 0

        self.local_time = 0
        self.move_start = 0
        self.old_pos = {item: (item.left, item.center_y) for item in self.items}

        self.window = arcade.get_window()

    @property
    def selected_id(self) -> int:
        return self._selected_id

    @selected_id.setter
    def selected_id(self, v: int) -> None:
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

    def sort(self, key: str, *, reverse: bool = False) -> None:
        if len(self.items) == 0:
            return
        selected = self.selected
        self.items.sort(key=attrgetter(key), reverse=reverse)
        self.selected_id = self.items.index(selected)

    def update(self, local_time: float) -> None:
        self.local_time = local_time
        current = self.selected
        current.left = ease_circout(self.old_pos[current][0], 0, perc(self.move_start, self.move_end, self.local_time))
        current.center_y = ease_circout(self.old_pos[current][1], self.window.height // 2, perc(self.move_start, self.move_end, self.local_time))
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
                up.left = ease_circout(self.old_pos[up][0], current.left - x_offset, perc(self.move_start, self.move_end, self.local_time))
                up.center_y = ease_circout(self.old_pos[up][1], y_offset + current.center_y, perc(self.move_start, self.move_end, self.local_time))
            if down_id < len(self.items):
                down = self.items[down_id]
                down.left = ease_circout(self.old_pos[down][0], current.left - x_offset, perc(self.move_start, self.move_end, self.local_time))
                down.center_y = ease_circout(self.old_pos[down][1], -y_offset + current.center_y, perc(self.move_start, self.move_end, self.local_time))

    def draw(self):
        self.sprite_list.draw()
