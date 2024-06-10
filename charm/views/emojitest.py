import logging

import arcade

from charm.lib.charm import GumWrapper
from charm.lib.digiview import DigiView
from charm.objects.emojilabel import EmojiLabel
from charm.lib.keymap import keymap

logger = logging.getLogger("charm")


class EmojiTestView(DigiView):
    def __init__(self, back: DigiView):
        super().__init__(fade_in=1, back=back)
        self.label: EmojiLabel

    def setup(self) -> None:
        super().presetup()
        self.label = EmojiLabel(
            "rainbow :rainbow:",
            anchor_x = 'center',
            x = self.window.center_x,
            y = self.window.center_y,
            color = arcade.color.BLACK,
            font_size = 48
        )
        self.gum_wrapper = GumWrapper(self.size)
        super().postsetup()

    def on_show_view(self) -> None:
        self.window.theme_song.volume = 0

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        super().on_key_press(symbol, modifiers)
        if keymap.back.pressed:
            self.go_back()

    def on_update(self, delta_time: float) -> None:
        super().on_update(delta_time)
        self.gum_wrapper.on_update(delta_time)

    def on_draw(self) -> None:
        super().predraw()
        self.gum_wrapper.draw()
        self.label.draw()
        super().postdraw()
