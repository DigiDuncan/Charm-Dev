from importlib.resources import files, as_file

import pyglet
import arcade_accelerate
import arcade

import charm.data.fonts
import charm.data.images
from charm.lib import charm_logger
from charm.lib.settings import settings
from charm.lib.utils import pyglet_img_from_path
from charm.lib.digiwindow import DigiWindow

# Fix font
pyglet.options["win32_disable_shaping"] = True
arcade_accelerate.bootstrap()


with as_file(files(charm.data.fonts) / "bananaslipplus.otf") as p:
    arcade.load_font(p)


class CharmGame(DigiWindow):
    def __init__(self):
        super().__init__(settings.resolution, "Charm", settings.fps)
        self.set_min_size(1, 1)
        icon = pyglet_img_from_path(files(charm.data.images) / "charm-icon32t.png")
        self.set_icon(icon)
        arcade.hitbox.algo_default = arcade.hitbox.algo_bounding_box


def main() -> None:
    charm_logger.setup()
    window = CharmGame()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
