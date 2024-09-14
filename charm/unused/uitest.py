import logging
from typing import cast

from arcade import Vec2, LRBT, types

from charm.lib.charm import GumWrapper
from charm.lib.digiview import DigiView, shows_errors, disable_when_focus_lost
from charm.lib.keymap import keymap
from charm.lib.anim import smerp

from charm.lib.mini_mint import RegionElement, Padding, Element, PaddingElement, VerticalElementList, BoxElement

logger = logging.getLogger("charm")


def make_padded_debug(padding: Padding = Padding(0, 20.0, 5.0, 5.0), min_size: Vec2 = Vec2(0.0, 100.0)) -> PaddingElement:
    return PaddingElement(padding, children=[BoxElement(colour=types.Color(255, 255, 255, 255))], min_size=min_size)


def make_empty(idx: int) -> Element:
    return Element(min_size=Vec2(0.0, 100.0))


class UiView(DigiView):
    def __init__(self, back: DigiView):
        super().__init__(fade_in=1, back=back)

        self._songs = ["asdoikaspldk" for _ in range(100)] # data we pick from when showing the list elements

        # The region of the screen taken up by the list. Includes space above and below screen so our
        # trick to fake an infitely scrollable list isn't spoiled
        self.root_ui_region = RegionElement(LRBT(0.0, 0.6, 0.0, 1.0))
        self.root_ui_region.bounds = self.window.rect
        self._base_region = self.root_ui_region.region
        
        # This structure is very difficult to follow. I think it ends up something like this?
        # root_ui_region = RegionElement
        #   self.element_list = VerticalElementList
        #     self.sublist = VerticalElementList
        #       PaddingElement
        #         BoxElement

        # Actual element list
        self.element_list: VerticalElementList = VerticalElementList(strict=False)
        self.root_ui_region.add_child(self.element_list)
        self.element_list_items: list[PaddingElement] = []

        # Update everything
        self.root_ui_region.layout()

        self.idx_offset = 0
        self.list_idx = 0
        self.sub_idx = 0

        self.scroll = 0.0
        self.sub_scroll = 0.0
        self.target_scroll = 0.0
        self.sub_target_scroll = 0.0
        self._scroll_decay = 16 # 1 - 25, slow -> fast

        self.select_time = 0.0
        self.selected_idx = -1
        self.deselect_time = 0.0

        self.spawn = -1.0
        self.speed = 0.75

        self.has_item_selected: bool = False

        self.sub_list_items: list[PaddingElement | None] = [None for _ in range(10)]
        self.sub_list: VerticalElementList = VerticalElementList(strict=True, min_size=Vec2(0.0, 60.0 * len(self.sub_list_items)))
        self.sub_list.add_child(make_padded_debug(Padding(2, 2, 2, 2)))

        self.place_items()

    def place_items(self) -> None:
        self.root_ui_region.bounds = self.window.rect

        self.idx_offset = int(self.window.center_y // 100) + 2
        vertical_count = self.idx_offset + 0.5 # We add the 0.5 so there will always be an odd number of elements in the list
        region_top = self.window.center_y + vertical_count * 100
        region_bottom = self.window.center_y - vertical_count * 100

        self.root_ui_region.region = self._base_region = self.root_ui_region.pixel_rect(bottom=region_bottom, top=region_top)

        curr_count = len(self.element_list_items)
        child_count = int(vertical_count*2)
        if child_count == curr_count:
            self.root_ui_region.layout(force=True)
            return
        self.element_list.empty()
        self.root_ui_region.layout(force=True)

        self.has_item_selected: bool = False

        if child_count < curr_count:
            self.element_list_items = self.element_list_items[:child_count]
        else:
            self.element_list_items.extend(make_padded_debug() for _ in range(child_count - curr_count))

        for element in self.element_list_items:
            self.element_list.add_child(element)

    def insert_sublist(self, idx: int) -> None:
        self.element_list.insert_child(self.sub_list, idx)
        self.select_time = self.window.time
        self.sub_target_scroll = 1

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
        elif keymap.navdown.pressed:
            if self.has_item_selected:
                self.sub_target_scroll += 1
                if self.sub_target_scroll >= len(self.sub_list_items):
                    self.has_item_selected = False
                    self.target_scroll = (self.target_scroll + 1) % len(self._songs)
                return
            self.target_scroll = (self.target_scroll + 1) % len(self._songs)
        elif keymap.navup.pressed:
            if self.has_item_selected:
                self.sub_target_scroll -= 1
                if self.sub_target_scroll <= 0:
                    self.has_item_selected = False
                    self.sub_target_scroll = 0.0
                return
            self.target_scroll = (self.target_scroll - 1) % len(self._songs)
        elif keymap.start.pressed:
            if self.has_item_selected:
                return
            self.has_item_selected = True
            self.insert_sublist(self.idx_offset + 1)
            self.selected_idx = int(self.target_scroll)
            self.sub_list.minimum_size = Vec2(0.0, 100.0)

    @shows_errors
    def on_update(self, delta_time: float) -> None:
        super().on_update(delta_time)
        self.gum_wrapper.on_update(delta_time)

        s = smerp(self.scroll, self.target_scroll, self._scroll_decay, delta_time)
        if abs(self.scroll - s) < 0.0001:
            self.scroll = self.target_scroll
        else:
            self.scroll = s

        ss = smerp(self.sub_scroll, self.sub_target_scroll, self._scroll_decay, delta_time)
        if abs(self.sub_scroll - ss) < 0.0001:
            self.sub_scroll = self.sub_target_scroll
        else:
            self.sub_scroll = ss

        sb = smerp(self.sub_list.minimum_size.y, len(self.sub_list_items) * 60.0, self._scroll_decay, delta_time)
        if abs(len(self.sub_list_items) * 60.0 - sb) < 0.0001:
            self.sub_list.minimum_size = Vec2(0.0, len(self.sub_list_items) * 60.0)
        else:
            self.sub_list.minimum_size = Vec2(0.0, sb)

        # This scroll value doesn't take into account the sub_list which will have to change.
        bounds_fraction = self.element_list_items[0].bounds.height/self.root_ui_region.bounds.height  # x/height is a constant we should store
        sub_fraction = (self.sub_list.bounds.height / len(self.sub_list_items)) / self.root_ui_region.bounds.height
        self.root_ui_region.region = self._base_region.move(0.0, (self.scroll % 1.0) * bounds_fraction + self.sub_scroll * sub_fraction)

        # This is really cursed and shouldn't be run every frame.
        # TODO: Add logic to place the sublists in the right place. Both the opening and closing one.
        focus_idx = int(self.scroll)
        start_idx = focus_idx - self.idx_offset

        if self.sub_list in self.element_list.children:
            self.element_list.remove_child(self.sub_list)
            sub_idx = self.selected_idx - start_idx + 1

            if 1 < sub_idx < len(self.element_list_items):
                self.element_list.insert_child(self.sub_list, sub_idx)
            else:
                self.has_item_selected = False
                self.sub_scroll = 0.0
                self.sub_target_scroll = 0.0

        for idx in range(len(self.element_list_items)):
            if start_idx + idx >= len(self._songs) or start_idx + idx < 0:
                self.element_list_items[idx].visible = False
                continue

            self.element_list_items[idx].visible = True

            # Elements should probably have a generic for children types
            item = cast(BoxElement, self.element_list_items[idx].children[0])
            item.text = str(start_idx + idx)
            item.colour = types.Color(10 * idx, 255 - 10 * idx, 100, 255)


    @shows_errors
    def on_draw(self) -> None:
        super().predraw()
        # Charm BG
        self.gum_wrapper.draw()
        self.root_ui_region.draw()
        super().postdraw()
