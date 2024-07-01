"""
A temporary stop gap between the old menu system and Mint.
"""
from __future__ import annotations
from typing import NamedTuple

from arcade import Rect, Vec2


class Padding(NamedTuple):
    left: float
    right: float
    bottom: float
    top: float


class Element:

    def __init__(self, parent: Element = None):
        self.strict: bool = False

        # The area the Element takes up. Not necessarily the area that an Element's children will work within
        # see PaddingElement, but a parent will work on an element based on its bounds. The area an Element draws
        # to is also not depended on the bounds, but they should mostly match to get correct behaviour.
        self.bounds: Rect = None

        self.children: list[Element] = []
        self.parent: Element = parent

        self.has_outdated_layout: bool = True

    def set_parent(self, parent: Element):
        pass

    def add_child(self, child: Element):
        pass

    def insert_child(self, child: Element, idx: int):
        pass

    def pop_child(self, idx: int):
        pass

    def remove_child(self, child: Element):
        pass

    def move_child(self, child: Element, idx: int):
        pass


class TextBox:
    pass


class VerticalElementList(Element):

    def __init__(self):
        super().__init__()
