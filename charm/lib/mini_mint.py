"""
A temporary stop gap between the old menu system and Mint.
"""
from __future__ import annotations
from typing import NamedTuple
from enum import Enum

from arcade import Rect, Vec2, get_window, LRBT, LBWH, XYWH, Window, draw_rect_filled, color, draw_rect_outline
from arcade.math import clamp

# TODO: add resize anchor
# TODO: add Subregion element
# TODO: add AnchorRegion element
# TODO: add Padding element


class Padding(NamedTuple):
    left: float
    right: float
    bottom: float
    top: float


# An alias for Vec2 which generally denotes a vector within the range 0.0 -> 1.0
Anchor = Vec2


DRAGON_PEACH = color.Color(255, 140, 120)


class Element:

    def __init__(self, parent: Element = None,
                 ideal_size: Vec2 | None = None,
                 min_size: Vec2 = Vec2(0.0, 0.0)):
        # The area the Element takes up. Not necessarily the area that an Element's children will work within
        # see PaddingElement, but a parent will work on an element based on its bounds. The area an Element draws
        # to is also not depended on the bounds, but they should mostly match to get correct behaviour.
        self._bounds: Rect = LBWH(0.0, 0.0, min_size.x, min_size.y)

        self._minimum_size: Vec2 = min_size
        self._ideal_size: Vec2 = ideal_size

        self.children: list[Element] = []
        self.parent: Element = parent

        self.has_outdated_layout: bool = True

        if parent is not None:
            self.parent.add_child(self)

    def add_child(self, child: Element):
        self.children.append(child)
        child.invalidate_layout()
        self.invalidate_layout()

    def empty(self):
        children = self.children[:]
        self.children = []
        for child in children:
            child.invalidate_layout()
        self.invalidate_layout()

    @property
    def bounds(self) -> Rect:
        return self._bounds

    @property
    def ideal_size(self) -> Vec2:
        return self._ideal_size

    @property
    def minimum_size(self) -> Vec2:
        return self._minimum_size

    @bounds.setter
    def bounds(self, new_bounds: Rect):
        if self._bounds == new_bounds:
            return
        self._bounds = new_bounds.min_size(
            self._minimum_size.x,
            self._minimum_size.y,
        )
        self.invalidate_layout()

    def _display(self):
        draw_rect_outline(self._bounds, DRAGON_PEACH, 4)

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


class RegionElement(Element):

    def __init__(self, region: Rect, ideal_size: Vec2 = Vec2(float('inf'), float('inf'))):
        super().__init__(ideal_size=ideal_size)
        self._region: Rect = region
        self._ideal_size = ideal_size
        self._sub_bounds: Rect = self._bounds
        self._win: Window = get_window()

    @property
    def region(self):
        return self._region

    @region.setter
    def region(self, new_region: Rect):
        self._region = new_region
        self.invalidate_layout()

    @property
    def sub_bounds(self) -> Rect:
        return self._sub_bounds

    def _calc_layout(self):
        window_rect = self.bounds
        region_bottom_left = self.region.left, self.region.bottom
        region_top_right = self.region.right, self.region.top
        left, bottom = window_rect.uv_to_position(region_bottom_left)
        right, top = window_rect.uv_to_position(region_top_right)

        self._sub_bounds = LRBT(left, right, bottom, top).max_size(self._ideal_size.x, self._ideal_size.y)
        for child in self.children:
            child.bounds = self._sub_bounds


class BoxElement(Element):

    def __init__(
            self,
            colour: color.Color, parent: Element = None,
            min_size: Vec2 = Vec2(0.0, 0.0)
    ):
        super().__init__(parent, min_size=min_size)
        self.colour: color.Color = colour

    def _display(self):
        draw_rect_filled(self._bounds, self.colour)


class AxisAnchor(Enum):
    BEGINNING = 0
    LEFT = 0
    TOP = 0

    CENTER = 1
    MIDDLE = 1

    BOTTOM = 2
    RIGHT = 2
    END = 2


class VerticalElementList(Element):
    # TODO: allow for varying priority in the children. Current they are all equally scaled based on the available size

    def __init__(self, anchor_axis: AxisAnchor = AxisAnchor.TOP, strict: bool = True):
        super().__init__()
        self._strict: bool = strict
        self._anchor_axis: AxisAnchor = anchor_axis

    @property
    def anchor_axis(self):
        return self._anchor_axis

    @anchor_axis.setter
    def anchor_axis(self, new_anchor: AxisAnchor):
        self._anchor_axis = new_anchor
        self.invalidate_layout()

    def insert_child(self, child: Element, idx: int = -1):
        self.children.insert(idx, child)
        self.invalidate_layout()
        child.invalidate_layout()

    def _calc_layout(self):
        # Todo make this smarter I got lazy

        if not self.children:
            return

        target_height = -float('inf') if self.ideal_size is None else self.ideal_size.y
        min_size = sum(child.minimum_size.y for child in self.children)

        free_height = self._bounds.height

        if not self._strict:
            free_height = max(free_height, min_size)

        if min_size < target_height < self._bounds.height:
            free_height = target_height

        child_height = free_height / len(self.children)

        heights = [max(child.minimum_size.y, child_height) for child in self.children]
        height = sum(heights)
        inset = 0.0 if len(self.children) == 1 else (free_height - height) / (len(self.children) - 1)

        left, width = self._bounds.left, self._bounds.width

        match self._anchor_axis:
            case AxisAnchor.TOP:
                top = self._bounds.top
                start_height = heights[0]
                self.children[0].bounds = LBWH(left, top - start_height, width, start_height)
                next_top = self.children[0].bounds.bottom
                for idx in range(1, len(self.children)):
                    next_height = heights[idx]
                    child = self.children[idx]
                    child.bounds = LBWH(left, next_top - next_height - inset, width, next_height)
                    next_top = child.bounds.bottom

            case AxisAnchor.CENTER:
                pass
            case AxisAnchor.BOTTOM:
                pass
