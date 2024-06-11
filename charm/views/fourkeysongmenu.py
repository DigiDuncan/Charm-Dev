from importlib.resources import files, as_file
import math
import logging
from pathlib import Path
from typing import Literal

import arcade
from arcade import Sprite, Text, color as colors

import charm.data.audio
import charm.data.images
from charm.lib.anim import ease_quartout, perc
from charm.lib.charm import GumWrapper
from charm.lib.digiview import DigiView, ignore_imgui, shows_errors
from charm.lib.errors import NoSongsFoundError
from charm.lib.gamemodes.sm import SMSong
from charm.lib.generic.song import Metadata
from charm.lib.keymap import keymap
from charm.lib.paths import songspath
from charm.objects.gif import GIF
from charm.objects.songmenu import SongMenu
from charm.views.fourkeysong import FourKeySongView

logger = logging.getLogger("charm")


class FourKeySongMenuView(DigiView):
    def __init__(self, back: DigiView):
        super().__init__(fade_in=0.5, back=back)

        self.album_art_buffer = self.window.width // 20
        self.static_time = 0.25

        self.songs: list[Metadata] = []
        self.menu: SongMenu | None = None

    @shows_errors
    def setup(self) -> None:
        super().presetup()
        self.gum_wrapper = GumWrapper(self.size)
        self.songs = []
        rootdir = Path(songspath / "4k")
        dir_list = [d for d in rootdir.glob('**/*') if d.is_dir()]
        for d in dir_list:
            charts = list(d.glob("*.ssc")) + list(d.glob("*.sm"))
            if charts:
                try:
                    songdata = SMSong.get_metadata(d)
                    self.songs.append(songdata)
                    continue
                except Exception as e:
                    logger.warn(e)
        try:
            self.setup_menu()
        except NoSongsFoundError:
            self.setup_no_menu()

        super().postsetup()

    def setup_menu(self) -> None:
        self.menu = SongMenu(self.songs)
        self.menu.sort("title")
        self.menu.selected_id = 0
        self.selection_changed = 0

        self.album_art = Sprite(self.menu.selected.album_art)
        self.album_art.right = self.size[0] - self.album_art_buffer
        self.album_art.original_bottom = self.album_art.bottom = self.size[1] // 2

        with as_file(files(charm.data.images) / "static.png") as p:
            self.static = GIF(p, 2, 5, 10, 30)
        self.static.right = self.size[0] - self.album_art_buffer
        self.static.original_bottom = self.album_art.bottom = self.size[1] // 2

    def setup_no_menu(self) -> None:
        self.nothing_text = Text(
            "No songs found!",
            int(self.window.center_x),
            int(self.window.center_y),
            colors.BLACK,
            64,
            align = "center",
            anchor_x = "center",
            anchor_y = "center",
            font_name = "bananaslip plus"
        )


    @shows_errors
    def on_show_view(self) -> None:
        super().on_show_view()

    @shows_errors
    def on_update(self, delta_time: float) -> None:
        super().on_update(delta_time)

        self.gum_wrapper.on_update(delta_time)

        if self.menu is not None:
            self.album_art.bottom = self.album_art.original_bottom + (math.sin(self.local_time * 2) * 25)
            self.static.bottom = self.album_art.original_bottom + (math.sin(self.local_time * 2) * 25)
            self.menu.update(self.local_time)
            self.static.update_animation(delta_time)

    @shows_errors
    @ignore_imgui
    def on_key_press(self, symbol: int, modifiers: int) -> None:
        super().on_key_press(symbol, modifiers)
        if keymap.navup.pressed:
            self.navup()
        elif keymap.navdown.pressed:
            self.navdown()
        elif keymap.start.pressed:
            if self.menu is not None:
                self.sfx.valid.play()
                songview = FourKeySongView(self.menu.selected.song.path, back=self)
                songview.setup()
                self.window.show_view(songview)
        elif keymap.back.pressed:
            self.go_back()

    def navup(self) -> None:
        self.nav(-1)

    def navdown(self) -> None:
        self.nav(+1)

    def nav(self, d: Literal[-1, 1]) -> None:
        if self.menu is not None:
            self.menu.selected_id += d
            self.sfx.select.play()
            self.selection_changed = self.local_time
            self.album_art.texture = self.menu.selected.album_art

    @shows_errors
    @ignore_imgui
    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> None:
        if self.menu is not None:
            self.menu.selected_id += int(scroll_y)
            self.sfx.select.play()

    @shows_errors
    @ignore_imgui
    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int) -> None:
        if self.menu is not None:
            self.sfx.valid.play()
            songview = FourKeySongView(self.menu.selected.song.path, back=self)
            songview.setup()
            self.window.show_view(songview)

    @shows_errors
    def on_draw(self) -> None:
        super().predraw()
        self.gum_wrapper.draw()

        if self.menu is not None:
            bottom = ease_quartout(self.size[1], 0, perc(0.5, 1.5, self.local_time))
            arcade.draw_lrbt_rectangle_filled(self.album_art.left - self.album_art_buffer, self.size[0], bottom, self.size[1], colors.WHITE[:3] + (127,))

            self.menu.draw()
            if self.local_time < self.selection_changed + self.static_time:
                self.static.draw()
            else:
                self.album_art.draw()
        else:
            self.nothing_text.draw()
        super().postdraw()
