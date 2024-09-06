from __future__ import annotations
from importlib.resources import files, as_file
import math

import arcade
from arcade import Sprite, SpriteList, Text, color as colors

import charm.data.images
from charm.lib.anim import ease_quartout, perc
from charm.lib.charm import GumWrapper
from charm.lib.digiview import DigiView, disable_when_focus_lost, shows_errors
from charm.lib.errors import NoSongsFoundError
from charm.lib.gamemodes.fnf import FNFSong
from charm.lib.keymap import keymap
from charm.objects.gif import GIF
from charm.objects.songmenu import SongMenu
from charm.lib.songloader import load_songs_fnf
from charm.unused.gameplay import GameView


class FNFSongMenuView(DigiView):
    def __init__(self, back: DigiView) -> None:
        super().__init__(fade_in=0.5, back=back)

        self.album_art_buffer = self.window.width // 20
        self.static_time = 0.25
        self.album_art: Sprite | None = None
        self.static: GIF | None = None
        self.album_art_list: SpriteList | None = None
        self.score_text: Text | None = None
        self.nothing_text: Text | None = None
        self.menu: SongMenu | None = None
        self.ready = False

    @shows_errors
    def setup(self) -> None:
        super().presetup()

        # Generate "gum wrapper" background
        self.gum_wrapper = GumWrapper()

        self.setup_menu()

        self.ready = True

        super().postsetup()

    def setup_menu(self) -> None:
        songs = load_songs_fnf()
        try:
            menu = SongMenu(songs)
        except NoSongsFoundError:
            self.setup_no_menu()
            return
        menu.sort("title")
        menu.selected_id = 0
        self.menu = menu
        self.selection_changed = 0

        print(songs)

        self.album_art_list = SpriteList(capacity=2)

        album_art = Sprite(menu.selected.album_art)
        album_art.right = self.size[0] - self.album_art_buffer
        album_art.original_bottom = self.size[1] // 2
        album_art.bottom = self.size[1] // 2
        self.album_art = album_art

        with as_file(files(charm.data.images) / "static.png") as p:
            static = GIF(p, 2, 5, 10, 30)
        static.right = self.size[0] - self.album_art_buffer
        static.original_bottom = self.size[1] // 2
        static.bottom = self.size[1] // 2
        self.static = static

        self.album_art_list.extend((self.album_art, self.static))

        self.score_text = Text(
            "N/A",
            album_art.center_x,
            album_art.bottom - 50,
            colors.BLACK,
            font_size = 48,
            font_name = "bananaslip plus",
            anchor_x = "center",
            anchor_y = "top",
            align = "center"
        )

    def setup_no_menu(self) -> None:
        self.nothing_text = Text(
            "No songs found!",
            self.window.width // 2,
            self.window.height // 2,
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

        if not self.ready:
            return

        self.gum_wrapper.on_update(delta_time)

        if self.menu is not None and self.album_art is not None and self.static is not None:
            self.album_art.bottom = self.album_art.original_bottom + (math.sin(self.local_time * 2) * 25)
            self.static.bottom = self.album_art.original_bottom + (math.sin(self.local_time * 2) * 25)
            self.menu.update(self.local_time)
            self.static.update_animation(delta_time)

    @shows_errors
    @disable_when_focus_lost(keyboard=True)
    def on_key_press(self, symbol: int, modifiers: int) -> None:
        super().on_key_press(symbol, modifiers)
        if keymap.navup.pressed:
            self.navup()
        elif keymap.navdown.pressed:
            self.navdown()
        elif keymap.start.pressed:
            self.start()
        elif keymap.back.pressed:
            self.go_back()
        elif keymap.dump_textures.pressed:
            self.window.save_atlas("hmmmmm.png")

    @shows_errors
    @disable_when_focus_lost(mouse=True)
    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> None:
        self.nav(int(scroll_y))

    @shows_errors
    @disable_when_focus_lost(mouse=True)
    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int) -> None:
        self.start()

    def navup(self) -> None:
        self.nav(-1)

    def navdown(self) -> None:
        self.nav(+1)

    def nav(self, d: int) -> None:
        if self.menu is not None and self.album_art is not None:
            self.menu.selected_id += d
            self.sfx.select.play()
            self.selection_changed = self.local_time
            self.album_art.texture = self.menu.selected.album_art

    def start(self) -> None:
        if self.menu is not None:
            self.sfx.valid.play()
            songview = GameView(FNFSong.parse(self.menu.selected.song.path), back = self)
            songview.setup()
            self.window.show_view(songview)

    @shows_errors
    def on_draw(self) -> None:
        super().predraw()
        if not self.ready:
            return

        # Charm BG
        self.gum_wrapper.draw()

        bottom = ease_quartout(self.size[1], 0, perc(0.5, 1.5, self.local_time))

        if self.menu is not None and self.album_art is not None and self.static is not None and self.score_text is not None:
            arcade.draw_lrbt_rectangle_filled(self.album_art.left - self.album_art_buffer, self.size[0], bottom, self.size[1], colors.WHITE[:3] + (127,))

            self.menu.draw()
            if self.local_time < self.selection_changed + self.static_time:
                self.static.visible = True
            else:
                self.static.visible = False

            self.album_art_list.draw()
            self.score_text.draw()
        elif self.nothing_text is not None:
            self.nothing_text.draw()
        super().postdraw()
