"""
Provides a Spritelist and Sprite subclass specifically for drawing the sprite's to always look directly at
the screen. The new Billboard works with any sprite type but the billboard sprite provides helper methods.
"""
from typing import Optional
from arcade import Sprite, SpriteList, TextureAtlas


class Billboard(Sprite):

    def __init__(self):
        super().__init__()

    @property
    def left(self) -> float:
        pass

    @property
    def right(self) -> float:
        pass

    @property
    def top(self) -> float:
        pass

    @property
    def bottom(self) -> float:
        pass

    @property
    def rect(self):
        pass


class BillboardList(SpriteList):

    def __init__(
            self,
            use_spatial_hash: bool = False,
            spatial_hash_cell_size: int = 128,
            atlas: Optional[TextureAtlas] = None,
            capacity: int = 100,
            lazy: bool = False,
            visible: bool = True,
    ):
        super().__init__(
            use_spatial_hash,
            spatial_hash_cell_size,
            atlas,
            capacity,
            lazy,
            visible
        )

    def _init_deferred(self) -> None:
        super()._init_deferred()

        # TODO: write billboard program

        # self.program = self.ctx.program(
        #
        # )
