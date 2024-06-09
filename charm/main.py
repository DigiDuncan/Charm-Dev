from types import ModuleType
from typing import cast

from importlib.resources import files, as_file

import pyglet
import arcade_accelerate
import arcade
import arcade.hitbox

import charm.data.fonts
import charm.data.images
from charm.lib.logging import setup_logging
from charm.lib.settings import settings
from charm.lib.utils import pyglet_img_from_resource
from charm.lib.digiwindow import DigiWindow

# Fix font
pyglet.options["win32_disable_shaping"] = True
arcade_accelerate.bootstrap()


with as_file(files(charm.data.fonts) / "bananaslipplus.otf") as f:
    arcade.text.load_font(str(f))


class CharmGame(DigiWindow):
    def __init__(self):
        super().__init__(settings.resolution, "Charm", settings.fps)
        self.set_min_size(1, 1)
        icon = pyglet_img_from_resource(cast(ModuleType, charm.data.images), "charm-icon32t.png")
        self.set_icon(icon)
        arcade.hitbox.algo_default = arcade.hitbox.algo_bounding_box


def main() -> None:
    setup_logging()
    window = CharmGame()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
