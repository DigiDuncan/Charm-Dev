import importlib.resources as pkg_resources
import math
from pathlib import Path
from typing import Literal

import arcade

import charm.data.audio
import charm.data.images
from charm.lib.settings import settings
from charm.lib.anim import ease_quartout
from charm.lib.charm import CharmColors, generate_gum_wrapper, move_gum_wrapper
from charm.lib.digiview import DigiView, ignore_imgui, shows_errors
from charm.lib.generic.song import Song
from charm.lib.gamemodes.fnf import FNFSong
from charm.lib.keymap import keymap
from charm.lib.paths import songspath
from charm.objects.gif import GIF
from charm.objects.songmenu import SongMenu
from charm.views.fnfsong import FNFSongView
from charm.lib.keymap import keymap


class FNFSongMenuView(DigiView):
    def __init__(self, back: DigiView) -> None:
        super().__init__(fade_in=0.5, bg_color=CharmColors.FADED_GREEN, back=back)

        self.album_art_buffer = self.window.width // 20
        self.static_time = 0.25
        self.hit_start = None
        self.album_art: arcade.Sprite = None
        self.static: arcade.AnimatedTimeBasedSprite = None
        self.menu: SongMenu = None

        self.ready = False

    @shows_errors
    def setup(self) -> None:
        super().setup()

        self.hit_start = None

        # Generate "gum wrapper" background
        self.logo_width, self.small_logos_forward, self.small_logos_backward = generate_gum_wrapper(self.size)

        self.songs: list[Song] = []
        rootdir = Path(songspath / "fnf")
        dir_list = [d for d in rootdir.glob('**/*') if d.is_dir()]
        for d in dir_list:
            k = d.name
            for diff, suffix in [("expert", "-ex"), ("hard", "-hard"), ("normal", ""), ("easy", "-easy")]:
                if (d / f"{k}{suffix}.json").exists():
                    songdata = FNFSong.get_metadata(d)
                    self.songs.append(songdata)
                    break

        self.menu = SongMenu(self.songs)
        self.menu.sort("title")
        self.menu.selected_id = 0
        self.selection_changed = 0

        if self.menu.items:
            self.album_art = arcade.Sprite(self.menu.selected.album_art)
            self.album_art.right = self.size[0] - self.album_art_buffer
            self.album_art.original_bottom = self.album_art.bottom = self.size[1] // 2
            with pkg_resources.path(charm.data.images, "static.png") as p:
                self.static = GIF(p, 2, 5, 10, 30)
            self.static.right = self.size[0] - self.album_art_buffer
            self.static.original_bottom = self.album_art.bottom = self.size[1] // 2

            self.score_text = arcade.Text("N/A", self.album_art.center_x, self.album_art.bottom - 50, arcade.color.BLACK,
                                      font_size = 48, font_name = "bananaslip plus", anchor_x = "center", anchor_y = "top",
                                      align = "center")

        self.nothing_text = arcade.Text("No songs found!", *self.window.center,
                                        arcade.color.BLACK, 64, align = "center", anchor_x = "center", anchor_y = "center",
                                        font_name = "bananaslip plus")

        self.ready = True

    @shows_errors
    def on_show_view(self) -> None:
        super().on_show_view()

    @shows_errors
    def on_update(self, delta_time) -> None:
        super().on_update(delta_time)

        if not self.ready:
            return

        move_gum_wrapper(self.logo_width, self.small_logos_forward, self.small_logos_backward, delta_time)

        if self.menu.items:
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
            arcade.play_sound(self.window.sounds["valid"], volume = settings.get_volume("sound"))
            songview = FNFSongView(self.menu.selected.song.path, back=self)
            songview.setup()
            self.window.show_view(songview)
        elif keymap.back.pressed:
            self.go_back()
        elif keymap.dump_textures.pressed:
            self.window.ctx.default_atlas.save("hmmmmm.png")

    def navup(self) -> None:
        self.nav(-1)

    def navdown(self) -> None:
        self.nav(+1)

    def nav(self, d: Literal[-1, 1]) -> None:
        self.menu.selected_id += d
        arcade.play_sound(self.window.sounds["select"], volume = settings.get_volume("sound"))
        self.selection_changed = self.local_time
        self.album_art.texture = self.menu.selected.album_art


    @shows_errors
    @ignore_imgui
    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> None:
        self.menu.selected_id += int(scroll_y)
        arcade.play_sound(self.window.sounds["select"])

    @shows_errors
    @ignore_imgui
    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int) -> None:
        arcade.play_sound(self.window.sounds["valid"])
        songview = FNFSongView(self.menu.selected.song.path, back=self)
        songview.setup()
        self.window.show_view(songview)

    @shows_errors
    def on_draw(self) -> None:
        self.window.default_camera.use()
        self.clear()

        if not self.ready:
            return

        # Charm BG
        self.small_logos_forward.draw()
        self.small_logos_backward.draw()

        bottom = ease_quartout(self.size[1], 0, 0.5, 1.5, self.local_time)

        if self.menu.items:
            arcade.draw_lrbt_rectangle_filled(self.album_art.left - self.album_art_buffer, self.size[0], bottom, self.size[1], arcade.color.WHITE[:3] + (127,))

            self.menu.draw()
            if self.local_time < self.selection_changed + self.static_time:
                self.static.draw()
            else:
                self.album_art.draw()
            self.score_text.draw()
        else:
            self.nothing_text.draw()

        super().on_draw()
