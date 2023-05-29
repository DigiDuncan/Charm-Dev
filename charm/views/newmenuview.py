import logging

import arcade

from charm.lib.charm import CharmColors, generate_gum_wrapper, move_gum_wrapper
from charm.lib.digiview import DigiView
from charm.objects.songmenu2 import SongMenu

logger = logging.getLogger("charm")


class NewMenuView(DigiView):
    def __init__(self, *args, **kwargs):
        super().__init__(fade_in=1, bg_color=CharmColors.FADED_GREEN, *args, **kwargs)
        self.song = None
        self.volume = 1
        self.menu: SongMenu = None

    def setup(self):
        super().setup()

        self.menu = SongMenu([])

        # Generate "gum wrapper" background
        self.logo_width, self.small_logos_forward, self.small_logos_backward = generate_gum_wrapper(self.size)

    def on_show_view(self):
        self.window.theme_song.volume = 0

    def on_key_press(self, symbol: int, modifiers: int):
        match symbol:
            case arcade.key.BACKSPACE:
                self.back.setup()
                self.window.show_view(self.back)
                arcade.play_sound(self.window.sounds["back"])

        return super().on_key_press(symbol, modifiers)

    def on_update(self, delta_time):
        super().on_update(delta_time)
        if self.window.keyboard[arcade.key.Y]:
            self.menu.min_factor += delta_time
        if self.window.keyboard[arcade.key.H]:
            self.menu.min_factor -= delta_time
        if self.window.keyboard[arcade.key.U]:
            self.menu.max_factor += delta_time
        if self.window.keyboard[arcade.key.J]:
            self.menu.max_factor -= delta_time
        if self.window.keyboard[arcade.key.I]:
            self.menu.offset += delta_time
        if self.window.keyboard[arcade.key.K]:
            self.menu.offset -= delta_time
        if self.window.keyboard[arcade.key.O]:
            self.menu.in_sin += delta_time
        if self.window.keyboard[arcade.key.L]:
            self.menu.in_sin -= delta_time
        if self.window.keyboard[arcade.key.P]:
            self.menu.out_sin += delta_time
        if self.window.keyboard[arcade.key.SEMICOLON]:
            self.menu.out_sin -= delta_time
        if self.window.keyboard[arcade.key.BRACKETLEFT]:
            self.menu.shift += delta_time
        if self.window.keyboard[arcade.key.APOSTROPHE]:
            self.menu.shift -= delta_time
        if self.window.keyboard[arcade.key.BRACKETRIGHT]:
            self.menu.move_forward += delta_time
        if self.window.keyboard[arcade.key.BACKSLASH]:
            self.menu.move_forward -= delta_time
        if self.window.keyboard[arcade.key.COMMA]:
            self.menu.y_shift += delta_time * 100
        if self.window.keyboard[arcade.key.PERIOD]:
            self.menu.y_shift -= delta_time * 100

        self.menu.update(delta_time)

        move_gum_wrapper(self.logo_width, self.small_logos_forward, self.small_logos_backward, delta_time)

    def on_draw(self):
        self.clear()
        self.camera.use()

        # Charm BG
        self.small_logos_forward.draw()
        self.small_logos_backward.draw()

        # Menu
        self.menu.draw()

        arcade.draw_text(f"{self.menu.min_factor=}\n{self.menu.max_factor=}\n{self.menu.offset=}\n{self.menu.in_sin=}\n{self.menu.out_sin=}\n{self.menu.shift=}\n{self.menu.move_forward=}",
                         self.window.width, self.window.height, arcade.color.BLACK, width = self.window.width, align = "right", anchor_x = "right", anchor_y = "top", multiline = True, font_size = 16)

        super().on_draw()
