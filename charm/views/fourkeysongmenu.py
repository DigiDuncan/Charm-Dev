import importlib.resources as pkg_resources
import math
from pathlib import Path

import arcade

import charm.data.audio
import charm.data.images
from charm.lib.anim import ease_quartout
from charm.lib.charm import CharmColors, generate_gum_wrapper, move_gum_wrapper
from charm.lib.digiview import DigiView, shows_errors
from charm.lib.gamemodes.sm import SMSong
from charm.lib.generic.song import Song
from charm.lib.keymap import get_keymap
from charm.lib.paths import songspath
from charm.lib.settings import settings
from charm.objects.songmenu import SongMenu
from charm.views.fourkeysong import FourKeySongView


class FourKeySongMenuView(DigiView):
    def __init__(self, *args, **kwargs):
        super().__init__(fade_in=0.5, bg_color=CharmColors.FADED_GREEN, *args, **kwargs)

        self.album_art_buffer = self.window.width // 20
        self.static_time = 0.25

    @shows_errors
    def setup(self):
        super().setup()

        self.hit_start = None

        # Generate "gum wrapper" background
        self.logo_width, self.small_logos_forward, self.small_logos_backward = generate_gum_wrapper(self.size)

        self.songs: list[Song] = []
        rootdir = Path(songspath / "4k")
        dir_list = [d for d in rootdir.glob('**/*') if d.is_dir()]
        for d in dir_list:
            k = d.stem
            try:
                if (d / f"{k}.ssc").exists():
                    songdata = SMSong.get_metadata(d)
                    self.songs.append(songdata)
                    continue
                if (d / f"{k}.sm").exists():
                    songdata = SMSong.get_metadata(d)
                    self.songs.append(songdata)
                    continue
            except Exception:
                continue

        self.menu = SongMenu(self.songs)
        self.menu.sort("title")
        self.menu.selected_id = 0
        self.selection_changed = 0

        self.album_art = arcade.Sprite(self.menu.selected.album_art)
        self.album_art.right = self.size[0] - self.album_art_buffer
        self.album_art.original_bottom = self.album_art.bottom = self.size[1] // 2

        with pkg_resources.path(charm.data.images, "static.gif") as p:
            self.static = arcade.load_animated_gif(p)
        self.static.right = self.size[0] - self.album_art_buffer
        self.static.original_bottom = self.album_art.bottom = self.size[1] // 2

    @shows_errors
    def on_show(self):
        return super().on_show()

    @shows_errors
    def on_update(self, delta_time):
        super().on_update(delta_time)

        move_gum_wrapper(self.logo_width, self.small_logos_forward, self.small_logos_backward, delta_time)

        self.album_art.bottom = self.album_art.original_bottom + (math.sin(self.local_time * 2) * 25)
        self.static.bottom = self.album_art.original_bottom + (math.sin(self.local_time * 2) * 25)
        self.menu.update(self.local_time)
        self.static.update_animation(delta_time)

    @shows_errors
    def on_key_press(self, symbol: int, modifiers: int):
        keymap = get_keymap()
        old_id = self.menu.selected_id
        match symbol:
            case arcade.key.UP:
                self.menu.selected_id -= 1
                arcade.play_sound(self.window.sounds["select"], volume = settings.get_volume("sound"))
            case arcade.key.DOWN:
                self.menu.selected_id += 1
                arcade.play_sound(self.window.sounds["select"], volume = settings.get_volume("sound"))
            case keymap.start:
                arcade.play_sound(self.window.sounds["valid"], volume = settings.get_volume("sound"))
                songview = FourKeySongView(self.menu.selected.song.path, back=self)
                songview.setup()
                self.window.show_view(songview)
            case keymap.back:
                arcade.play_sound(self.window.sounds["back"], volume = settings.get_volume("sound"))
                self.back.setup()
                self.window.show_view(self.back)
        if old_id != self.menu.selected_id:
            self.selection_changed = self.local_time
            self.album_art.texture = self.menu.selected.album_art

        return super().on_key_press(symbol, modifiers)

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        self.menu.selected_id += int(scroll_y)
        arcade.play_sound(self.window.sounds["select"])

    @shows_errors
    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        arcade.play_sound(self.window.sounds["valid"])
        songview = FourKeySongView(self.menu.selected.song.path, back=self)
        songview.setup()
        self.window.show_view(songview)

    @shows_errors
    def on_draw(self):
        self.window.camera.use()
        self.clear()

        # Charm BG
        self.small_logos_forward.draw()
        self.small_logos_backward.draw()

        bottom = ease_quartout(self.size[1], 0, 0.5, 1.5, self.local_time)
        arcade.draw_lrbt_rectangle_filled(self.album_art.left - self.album_art_buffer, self.size[0], bottom, self.size[1], arcade.color.WHITE[:3] + (127,))

        self.menu.draw()
        if self.local_time < self.selection_changed + self.static_time:
            self.static.draw()
        else:
            self.album_art.draw()

        super().on_draw()
