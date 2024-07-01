import logging

from arcade import Vec2, LRBT

from charm.lib.charm import GumWrapper
from charm.lib.digiview import DigiView, shows_errors, disable_when_focus_lost
from charm.lib.keymap import keymap

from charm.lib.item_list import WindowRegionElement, VerticalElementList

logger = logging.getLogger("charm")


class UiView(DigiView):
    def __init__(self, back: DigiView):
        super().__init__(fade_in=1, back=back)

        self.root_ui_region: WindowRegionElement = WindowRegionElement(LRBT(0.0, 0.65, 0.0, 1.0))
        self.element_list: VerticalElementList = VerticalElementList()
        self.root_ui_region.add_child(self.element_list)

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)
        self.root_ui_region.invalidate_layout()

    @shows_errors
    def setup(self) -> None:
        super().presetup()
        self.gum_wrapper = GumWrapper()
        super().postsetup()

    def on_show_view(self) -> None:
        self.window.theme_song.volume = 0

    @shows_errors
    @disable_when_focus_lost(keyboard=True)
    def on_key_press(self, symbol: int, modifiers: int) -> None:
        super().on_key_press(symbol, modifiers)
        if keymap.back.pressed:
            self.go_back()

    @shows_errors
    def on_update(self, delta_time: float) -> None:
        super().on_update(delta_time)
        self.gum_wrapper.on_update(delta_time)

    @shows_errors
    def on_draw(self) -> None:
        super().predraw()
        # Charm BG
        self.gum_wrapper.draw()
        self.root_ui_region.draw()
        super().postdraw()