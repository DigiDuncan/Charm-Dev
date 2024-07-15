import logging

import arcade.key
from arcade import Vec2, LRBT, color

from charm.lib.charm import GumWrapper
from charm.lib.digiview import DigiView, shows_errors, disable_when_focus_lost
from charm.lib.keymap import keymap
from charm.lib.anim import perc, ease_expoout, smerp

from charm.lib.mini_mint import RegionElement, Padding, Element, PaddingElement, VerticalElementList, BoxElement

logger = logging.getLogger("charm")


def make_padded_debug(idx: int, padding: Padding = Padding(0, 20.0, 5.0, 5.0), blue: int = 100, min_size: Vec2 = Vec2(0.0, 100.0)):
    return PaddingElement(padding, children=[BoxElement(colour=color.Color(10 * idx, 255 - 10 * idx, blue, 255))], min_size=min_size)

def make_padded_empty(idx: int):
    return Element(min_size=Vec2(0.0, 100.0))

class UiView(DigiView):
    def __init__(self, back: DigiView):
        super().__init__(fade_in=1, back=back)

        self._songs = ["asdoikaspldk" for _ in range(100)] # data we pick from when showing the list elements

        # The region of the screen taken up by the list. Includes space above and below screen so our
        # trick to fake an infitely scrollable list isn't spoiled
        self.root_ui_region: RegionElement = RegionElement(LRBT(0.0, 0.6, 0.0, 1.0))
        self.root_ui_region.bounds = self.window.rect
        self.root_ui_region.region = self._base_region = self.root_ui_region.pixel_rect(bottom=-100.0, top=self.window.height+100.0)

        # Actual element list
        self.element_list: VerticalElementList = VerticalElementList(strict=False)
        self.root_ui_region.add_child(self.element_list)

        # Update everything
        self.root_ui_region.layout()

        child_count = self.element_list.bounds.height // 100

        self.element_list.empty()
        for _ in range(int(child_count) + 1):
            self.element_list.add_child(make_padded_debug(_))

        self._add_time = 0.0

        self.list_idx = 0
        self.sub_idx = 0

        self.scroll = 0.0
        self.target_scroll = 0.0
        self._scroll_decay = 16 # 1 - 25, slow -> fast

        self.select_time = 0.0

        self.spawn = -1.0
        self.speed = 0.75
        self.sub_list: VerticalElementList = VerticalElementList(strict=True)

    def place_items(self):
        self.root_ui_region.bounds = self.window.rect
        self.root_ui_region.region = self._base_region = self.root_ui_region.pixel_rect(bottom=-100.0, top=self.window.height+100.0)
        self.root_ui_region.layout()

        child_count = self.element_list.bounds.height // 100

        self.element_list.empty()
        for _ in range(int(child_count) + 1):
            self.element_list.add_child(make_padded_debug(_))

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)
        self.place_items()

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
        if keymap.navdown.pressed:
            self.target_scroll = (self.target_scroll + 1) % len(self._songs)
        if keymap.navup.pressed:
            self.target_scroll = (self.target_scroll - 1) % len(self._songs)

    @shows_errors
    def on_update(self, delta_time: float) -> None:
        super().on_update(delta_time)
        self.gum_wrapper.on_update(delta_time)

        s = smerp(self.scroll, self.target_scroll, self._scroll_decay, delta_time)
        print(s, self.scroll, self.target_scroll)
        if abs(self.scroll - s) < 0.00001:
            self.scroll = self.target_scroll
        else:
            self.scroll = s

        # This scroll value doesn't take into account the sub_list which will have to change.
        self.root_ui_region.region = self._base_region.move(0.0, (self.scroll % 1.0) * 100.0/self.root_ui_region.bounds.height)

        # This is really cursed and shouldn't be run every frame. Also it relies on the len of the element list which
        # will change when the sub-list gets added
        focus_idx = int(self.scroll)
        start_idx = focus_idx - len(self.element_list.children) // 2 + 1
        for idx in range(len(self.element_list.children)):
            # Elements should probably have a generic for children types
            item = self.element_list.children[idx].children[0]
            item.text = str(start_idx + idx)
            item.colour = color.Color(10 * idx, 255 - 10 * idx, 100, 255)
            if start_idx + idx >= len(self._songs) or start_idx + idx < 0:
                item.colour = color.Color(0, 0, 0, 0)

    @shows_errors
    def on_draw(self) -> None:
        super().predraw()
        # Charm BG
        self.gum_wrapper.draw()
        self.root_ui_region.draw()
        super().postdraw()
