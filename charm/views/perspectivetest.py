import importlib.resources as pkg_resources
import logging

from math import cos, sin, radians

import arcade

from charm.lib.charm import CharmColors, GumWrapper
from charm.lib.digiview import DigiView, shows_errors, ignore_imgui
from charm.lib.keymap import keymap

from charm.lib.perp_cam import PerspectiveProjector
import charm.data.images

logger = logging.getLogger("charm")


CAM_SPEED = 400.0


class PerspectiveView(DigiView):
    def __init__(self, back: DigiView):
        super().__init__(fade_in=1, bg_color=CharmColors.FADED_GREEN, back=back)

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
        self.gum_wrapper = GumWrapper(self.size)

    def on_show_view(self) -> None:
        self.window.theme_song.volume = 0

    @shows_errors
    @ignore_imgui
    def on_key_press(self, symbol: int, modifiers: int) -> None:
        super().on_key_press(symbol, modifiers)
        if keymap.back.pressed:
            self.go_back()


    @shows_errors
    @ignore_imgui
    def on_key_release(self, symbol: int, modifiers: int) -> None:
        super().on_key_release(symbol, modifiers)
        match symbol:
            case _:
                return

    @shows_errors
    def on_update(self, delta_time) -> None:
        super().on_update(delta_time)

        self.gum_wrapper.on_update(delta_time)

    @shows_errors
    def on_draw(self) -> None:
        self.window.camera.use()
        self.clear()

        # Charm BG
        self.gum_wrapper.draw()

        with self.proj.activate():
            self.asdsa.draw(pixelated=True)

        super().on_draw()
