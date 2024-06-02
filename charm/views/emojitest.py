import logging

import arcade

from charm.lib.charm import CharmColors, generate_gum_wrapper, move_gum_wrapper
from charm.lib.digiview import DigiView
from charm.objects.emojilabel import EmojiLabel
from charm.lib.keymap import keymap

logger = logging.getLogger("charm")


class EmojiView(DigiView):
    def __init__(self, back: DigiView):
        super().__init__(fade_in=1, bg_color=CharmColors.FADED_GREEN, back=back)
        self.song = None

    def setup(self) -> None:
        super().setup()

        self.label = EmojiLabel("rainbow :rainbow:", anchor_x = 'center',
                                x = self.window.center_x, y = self.window.center_y,
                                color = arcade.color.BLACK, font_size = 48)

        # Generate "gum wrapper" background
        self.logo_width, self.small_logos_forward, self.small_logos_backward = generate_gum_wrapper(self.size)

    def on_show_view(self) -> None:
        self.window.theme_song.volume = 0

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        super().on_key_press(symbol, modifiers)
        if keymap.back.pressed:
            self.go_back()

    def on_update(self, delta_time) -> None:
        super().on_update(delta_time)

        move_gum_wrapper(self.logo_width, self.small_logos_forward, self.small_logos_backward, delta_time)

    def on_draw(self) -> None:
        self.window.camera.use()
        self.clear()

        # Charm BG
        self.small_logos_forward.draw()
        self.small_logos_backward.draw()

        self.label.draw()

        super().on_draw()
