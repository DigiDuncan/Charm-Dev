from pyglet.math import Vec2
from charm.lib.mini_mint import Element


class SubListElement(Element[Element | None, Element]):

    def __init__(self, parent: Element = None, min_size: Vec2 = Vec2()):
        super().__init__(parent, min_size)
