import logging

import arcade

from charm.lib.charm import CharmColors, generate_gum_wrapper, move_gum_wrapper
from charm.lib.digiview import DigiView
from charm.objects.emojilabel import EmojiLabel

logger = logging.getLogger("charm")


class EmojiView(DigiView):
    def __init__(self, *args, **kwargs):
        super().__init__(fade_in=1, bg_color=CharmColors.FADED_GREEN, *args, **kwargs)
        self.song = None
        self.volume = 1

    def setup(self):
        super().setup()

        self.label = EmojiLabel("pencil :pencil2:", anchor_x = 'center',
                                x = self.window.width / 2, y = self.window.height / 2,
                                color = arcade.color.BLACK, font_size = 48)

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

        move_gum_wrapper(self.logo_width, self.small_logos_forward, self.small_logos_backward, delta_time)

    def on_draw(self):
        self.window.camera.use()
        self.clear()

        # Charm BG
        self.small_logos_forward.draw()
        self.small_logos_backward.draw()

        self.label.draw()

        super().on_draw()
