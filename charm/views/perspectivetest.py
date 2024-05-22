import importlib.resources as pkg_resources
import logging

from math import cos, sin, radians

import arcade

from charm.lib.charm import CharmColors, generate_gum_wrapper, move_gum_wrapper
from charm.lib.digiview import DigiView, shows_errors, ignore_imgui

from charm.lib.perp_cam import PerspectiveProjector

logger = logging.getLogger("charm")


CAM_SPEED = 400.0


class PerspectiveView(DigiView):
    def __init__(self, *args, **kwargs):
        super().__init__(fade_in=1, bg_color=CharmColors.FADED_GREEN, *args, **kwargs)
        self.volume = 1

        self.bingo = arcade.SpriteSolidColor(100, 500, 0, 0)
        self.bingo.bottom = 0.0
        self.asdsa = arcade.SpriteList()
        self.asdsa.append(self.bingo)

        self.proj = PerspectiveProjector()

        self.phi = 45.0

        data = self.proj.view
        data_h_fov = 0.5 * self.proj.projection.fov

        data.position = (0.0, -10.0 * sin(radians(self.phi)), 10.0 * cos(radians(self.phi)))
        data.forward, data.up = arcade.camera.grips.rotate_around_right(data, -self.phi - data_h_fov)


    @shows_errors
    def setup(self):
        super().setup()

        # Generate "gum wrapper" background
        self.logo_width, self.small_logos_forward, self.small_logos_backward = generate_gum_wrapper(self.size)

    def on_show_view(self):
        self.window.theme_song.volume = 0

    @shows_errors
    @ignore_imgui
    def on_key_press(self, symbol: int, modifiers: int):
        match symbol:
            case arcade.key.BACKSPACE:
                self.back.setup()
                self.window.show_view(self.back)
                arcade.play_sound(self.window.sounds["back"])

        return super().on_key_press(symbol, modifiers)

    @shows_errors
    @ignore_imgui
    def on_key_release(self, _symbol: int, _modifiers: int):
        match _symbol:
            case _:
                return

    @shows_errors
    def on_update(self, delta_time):
        super().on_update(delta_time)

        move_gum_wrapper(self.logo_width, self.small_logos_forward, self.small_logos_backward, delta_time)

    @shows_errors
    def on_draw(self):
        self.window.camera.use()
        self.clear()

        # Charm BG
        self.small_logos_forward.draw()
        self.small_logos_backward.draw()

        super().on_draw()

        with self.proj.activate():
            self.asdsa.draw(pixelated=True)
