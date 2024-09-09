from arcade.types import Color
from arcade import draw_rect_filled

from charm.lib.mini_mint import Element

from charm.ui.settings.settings_tab import SettingsTabElement

OVERLAY_COLOR = Color(0, 0, 0, 125)

class SettingsMenuElement(Element[SettingsTabElement]):

    def __init__(self):
        super().__init__()
        pass

    def _display(self) -> None:
        draw_rect_filled(self.bounds, OVERLAY_COLOR)
