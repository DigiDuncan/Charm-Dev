"""
A temporary stop gap between the old menu system and Mint.
"""
from __future__ import annotations
from typing import NamedTuple

from arcade import Rect, Vec2, get_window, LRBT, LBWH, Window, draw_rect_filled, color

# TODO: add resize anchor
# TODO: add Subregion element
# TODO: add AnchorRegion element
# TODO: add Padding element


class Padding(NamedTuple):
    left: float
    right: float
    bottom: float
    top: float


class Element:

    def __init__(self, parent: Element = None,
                 target_size: Vec2 | None = None,
                 min_size: Vec2 = Vec2(0.0, 0.0),
                 max_size: Vec2 = Vec2(float('inf'), float('inf'))):
        # The area the Element takes up. Not necessarily the area that an Element's children will work within
        # see PaddingElement, but a parent will work on an element based on its bounds. The area an Element draws
        # to is also not depended on the bounds, but they should mostly match to get correct behaviour.
        self._bounds: Rect = LBWH(0.0, 0.0, min_size.x, min_size.y)

        self._minimum_size: Vec2 = min_size
        self._target_size: Vec2 = target_size
        self._maximum_size: Vec2 = max_size

        self.children: list[Element] = []
        self.parent: Element = parent

        self.has_outdated_layout: bool = True

        if parent is not None:
            self.parent.add_child(self)

    def add_child(self, child: Element):
        self.children.append(child)
        child.invalidate_layout()
        self.invalidate_layout()

    @property
    def bounds(self) -> Rect | None:
        return self._bounds

    @property
    def target_size(self) -> Vec2:
        return self._target_size

    @property
    def maximum_size(self) -> Vec2:
        return self._maximum_size

    @property
    def minimum_size(self) -> Vec2:
        return self._minimum_size

    @bounds.setter
    def bounds(self, new_bounds: Rect):
        self._bounds = new_bounds.clamp_size(
            self._minimum_size.x, self._maximum_size.x,
            self._minimum_size.y, self._maximum_size.y
        )
        self.invalidate_layout()

    def _display(self):
        pass

    def _calc_layout(self):
        pass

    def draw(self):
        if self.has_outdated_layout:
            self.layout()

        self._display()
        for child in self.children:
            child.draw()

    def layout(self):
        self._calc_layout()
        self.has_outdated_layout = False

    def invalidate_layout(self):
        self.has_outdated_layout = True


class WindowRegionElement(Element):

    def __init__(self, region: Rect):
        super().__init__()
        self._region: Rect = region
        self._win: Window = get_window()

    @property
    def region(self):
        return self._region

    @region.setter
    def region(self, new_region: Rect):
        self._region = new_region
        self.invalidate_layout()

    def _display(self):
        draw_rect_filled(self._bounds, color.ORANGE)

    def _calc_layout(self):
        window_rect = self._win.rect
        region_bottom_left = self.region.left, self.region.bottom
        region_top_right = self.region.right, self.region.top
        left, bottom = window_rect.uv_to_position(region_bottom_left)
        right, top = window_rect.uv_to_position(region_top_right)

        self._bounds = LRBT(left, right, bottom, top)
        for child in self.children:
            child.bounds = self.bounds


class BoxElement(Element):

    def __init__(
            self,
            colour: color.Color, parent: Element,
            min_size: Vec2 = Vec2(0.0, 0.0), max_size: Vec2 = Vec2(float('inf'), float('inf'))
    ):
        super().__init__(parent, min_size=min_size, max_size=max_size)
        self.colour: color.Color = colour

    def _display(self):
        draw_rect_filled(self.bounds, self.colour)


class VerticalElementList(Element):

    def __init__(self):
        super().__init__()

    def insert_child(self, child: Element, idx: int = -1):
        self.children.insert(idx, child)
        self.invalidate_layout()
        child.invalidate_layout()

    def _calc_layout(self):
        ideal_height = sum(child.target_size.y for child in self.children)
        min_height = sum(child.minimum_size.y for child in self.children)
        max_height = sum(child.maximum_size.y for child in self.children)


