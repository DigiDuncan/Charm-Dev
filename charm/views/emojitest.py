import logging

import arcade

from charm.lib.charm import CharmColors, GumWrapper
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
        self.gum_wrapper = GumWrapper(self.size)

    def on_show_view(self) -> None:
        self.window.theme_song.volume = 0

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        super().on_key_press(symbol, modifiers)
        if keymap.back.pressed:
            self.go_back()

    def on_update(self, delta_time) -> None:
        super().on_update(delta_time)

        self.gum_wrapper.on_update(delta_time)

    def on_draw(self) -> None:
        self.window.camera.use()
        self.clear()

        # Charm BG
        self.gum_wrapper.draw()

        self.label.draw()

        super().on_draw()
