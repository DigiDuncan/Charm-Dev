import logging

import arcade.key
from arcade import Vec2, LRBT, color

from charm.lib.charm import GumWrapper
from charm.lib.digiview import DigiView, shows_errors, disable_when_focus_lost
from charm.lib.keymap import keymap

from charm.lib.mini_mint import RegionElement, VerticalElementList, BoxElement

logger = logging.getLogger("charm")


class UiView(DigiView):
    def __init__(self, back: DigiView):
        super().__init__(fade_in=1, back=back)

        self._base_region = LRBT(0.0, 0.65, 0.2, 0.8)
        self._test_offset = 0.0

        self.root_ui_region: RegionElement = RegionElement(self._base_region)
        self.root_ui_region.bounds = self.window.rect

        self.element_list: VerticalElementList = VerticalElementList(strict=False)
        self.root_ui_region.add_child(self.element_list)

        self.root_ui_region.layout()
        self.element_list.layout()

        child_count = self.element_list.bounds.height // 100

        self.element_list.empty()
        for _ in range(int(child_count)):
            self.element_list.add_child(BoxElement(colour=color.Color.random(a=255), min_size=Vec2(0.0, 100.0)))
        self.element_list.add_child(BoxElement(colour=(0, 0, 0, 0)))

        self.sub_list: VerticalElementList = VerticalElementList(strict=True)

        self._ctrl_press: bool = False

        self._add_time = 0.0

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)

        self.root_ui_region.bounds = self.window.rect
        self.root_ui_region.invalidate_layout()

        child_count = self.element_list.bounds.height // 100

        if child_count + 1 == len(self.element_list.children):
            return

        self.element_list.empty()
        for _ in range(int(child_count) + 1):
            self.element_list.add_child(BoxElement(colour=color.Color.random(a=255), min_size=Vec2(0.0, 100.0)))

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        if scroll_y:
            shift = scroll_y / 100.0
            if self._ctrl_press:
                self.sub_list._minimum_size = Vec2(0.0, max(0.0, self.sub_list.minimum_size.y + scroll_y * 10.0))
                self.element_list.invalidate_layout()
                self.sub_list.invalidate_layout()
            else:
                self._test_offset += shift
                self.root_ui_region.region = self._base_region.move(0.0, self._test_offset)

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
        elif arcade.key.LCTRL:
            self._ctrl_press = True

    @shows_errors
    @disable_when_focus_lost(keyboard=True)
    def on_key_release(self, symbol: int, modifiers: int) -> None:
        super().on_key_release(symbol, modifiers)
        if arcade.key.LCTRL:
            self._ctrl_press = False

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
