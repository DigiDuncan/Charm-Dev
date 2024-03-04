import importlib.resources as pkg_resources

import pyglet

import arcade_accelerate
arcade_accelerate.bootstrap()

# Fix font
pyglet.options["win32_disable_shaping"] = True
import arcade
arcade.pyglet.options["win32_disable_shaping"] = True
import arcade.hitbox

import charm
import charm.data.fonts
import charm.data.images
from charm.lib.logging import setup_logging
from charm.lib.settings import settings
from charm.lib.utils import pyglet_img_from_resource
from charm.lib.digiwindow import DigiWindow

from .views.title import TitleView

SCREEN_WIDTH = settings.resolution.width
SCREEN_HEIGHT = settings.resolution.height
FPS_CAP = settings.fps
SCREEN_TITLE = "Charm"


with pkg_resources.path(charm.data.fonts, "bananaslipplus.otf") as p:
    arcade.text.load_font(str(p))


class CharmGame(DigiWindow):
    def __init__(self):
        super().__init__((SCREEN_WIDTH, SCREEN_HEIGHT), SCREEN_TITLE, FPS_CAP, None)

        icon = pyglet_img_from_resource(charm.data.images, "charm-icon32t.png")
        self.set_icon(icon)

        sfx = ["back", "select", "valid"]
        err = ["error", "warning", "info"]

        # Menu sounds
        for soundname in sfx:
            with pkg_resources.path(charm.data.audio, f"sfx-{soundname}.wav") as p:
                self.sounds[soundname] = arcade.Sound(p)
        for soundname in err:
            with pkg_resources.path(charm.data.audio, f"error-{soundname}.wav") as p:
                self.sounds["error-" + soundname] = arcade.Sound(p)

        arcade.hitbox.default_algorithm = arcade.hitbox.algo_bounding_box

        self.initial_view = TitleView()


def main():
    setup_logging()
    window = CharmGame()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
