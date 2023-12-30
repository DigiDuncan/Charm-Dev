import importlib.resources as pkg_resources

import arcade

from charm.lib.charm import CharmColors, generate_gum_wrapper, move_gum_wrapper
from charm.lib.digiview import DigiView
from charm.lib.keymap import get_keymap

import charm.data.subtitle
from charm.objects.lyric import LyricAnimator


class SubtitleView(DigiView):
    def __init__(self, *args, **kwargs):
        super().__init__(fade_in=1, bg_color=CharmColors.FADED_GREEN, *args, **kwargs)
        self.song = None
        self.volume = 1

    def setup(self):
        super().setup()

        with pkg_resources.path(charm.data.subtitle, "crossing_field_8bit.mp3") as p:
            self._song = arcade.Sound(p)

        with pkg_resources.path(charm.data.subtitle, "crossing_field.ass") as p:
            self.lyric_animator = LyricAnimator(p)

        # Generate "gum wrapper" background
        self.logo_width, self.small_logos_forward, self.small_logos_backward = generate_gum_wrapper(self.size)

    def on_show(self):
        self.window.theme_song.volume = 0
        self.song = arcade.play_sound(self._song, self.volume, loop=False)

    def on_key_press(self, symbol: int, modifiers: int):
        keymap = get_keymap()
        match symbol:
            case keymap.back:
                self.back.setup()
                self.window.show_view(self.back)
                arcade.play_sound(self.window.sounds["back"])

        return super().on_key_press(symbol, modifiers)

    def on_update(self, delta_time):
        super().on_update(delta_time)

        if self.song:
            self.lyric_animator.update(self.song.time)

        move_gum_wrapper(self.logo_width, self.small_logos_forward, self.small_logos_backward, delta_time)

    def on_draw(self):
        self.window.camera.use()
        self.clear()

        # Charm BG
        self.small_logos_forward.draw()
        self.small_logos_backward.draw()

        arcade.draw_lrbt_rectangle_filled(
            0, self.window.width, 0, self.window.height,
            (0, 0, 0, 127)
        )

        self.lyric_animator.draw()

        super().on_draw()
