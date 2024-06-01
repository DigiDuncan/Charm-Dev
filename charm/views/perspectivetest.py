import importlib.resources as pkg_resources
import logging

from math import cos, sin, radians

import arcade

from pyglet.math import Vec3


from charm.lib.charm import CharmColors, generate_gum_wrapper, move_gum_wrapper
from charm.lib.digiview import DigiView, shows_errors, ignore_imgui

from charm.lib.perp_cam import PerspectiveProjector
import charm.data.images

logger = logging.getLogger("charm")


CAM_SPEED = 400.0


class PerspectiveView(DigiView):
    def __init__(self, *args, **kwargs):
        super().__init__(fade_in=1, bg_color=CharmColors.FADED_GREEN, *args, **kwargs)
        self.volume = 1

        with pkg_resources.path(charm.data.images, "no_image_found.png") as p:
            self.bingo = arcade.Sprite(p, center_y=250)
        self.bingo.bottom = 0.0
        self.asdsa = arcade.SpriteList()
        self.asdsa.append(self.bingo)

        self.proj = PerspectiveProjector()
        self.proj.projection.far = 10000.0

        self.view_angle = 85.0
        self.view_dist = 100.0

        data = self.proj.view
        data_h_fov = 0.5 * self.proj.projection.fov

        look_radians = radians(self.view_angle - data_h_fov)

        data.position = (0.0, -self.view_dist * sin(look_radians), self.view_dist * cos(look_radians))
        data.up, data.forward = arcade.camera.grips.rotate_around_right(data, -self.view_angle)

    @shows_errors
    def setup(self) -> None:
        super().setup()

        # Generate "gum wrapper" background
        self.logo_width, self.small_logos_forward, self.small_logos_backward = generate_gum_wrapper(self.size)

    def on_show_view(self) -> None:
        self.window.theme_song.volume = 0

    @shows_errors
    @ignore_imgui
    def on_key_press(self, symbol: int, modifiers: int) -> None:
        match symbol:
            case arcade.key.BACKSPACE:
                self.back.setup()
                self.window.show_view(self.back)
                arcade.play_sound(self.window.sounds["back"])

        super().on_key_press(symbol, modifiers)

    @shows_errors
    @ignore_imgui
    def on_key_release(self, _symbol: int, _modifiers: int) -> None:
        match _symbol:
            case _:
                return

    @shows_errors
    def on_update(self, delta_time) -> None:
        super().on_update(delta_time)

        move_gum_wrapper(self.logo_width, self.small_logos_forward, self.small_logos_backward, delta_time)

    @shows_errors
    def on_draw(self) -> None:
        self.window.camera.use()
        self.clear()

        # Charm BG
        self.small_logos_forward.draw()
        self.small_logos_backward.draw()

        with self.proj.activate():
            self.asdsa.draw(pixelated=True)

        super().on_draw()
