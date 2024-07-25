from pyglet.math import Vec2
from charm.lib.mini_mint import Element


class SubListElement(Element):

    def __init__(self, parent: Any = None, ideal_size: Vec2 | None = None, min_size: Vec2 = Vec2()):
        super().__init__(parent, ideal_size, min_size)
