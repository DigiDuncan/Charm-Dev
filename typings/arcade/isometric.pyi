"""
This type stub file was generated by pyright.
"""

from arcade.shape_list import ShapeElementList
from typing import Tuple
from arcade.types import RGBA255

def isometric_grid_to_screen(tile_x: int, tile_y: int, width: int, height: int, tile_width: int, tile_height: int) -> Tuple[int, int]:
    ...

def screen_to_isometric_grid(screen_x: int, screen_y: int, width: int, height: int, tile_width: int, tile_height: int) -> Tuple[int, int]:
    ...

def create_isometric_grid_lines(width: int, height: int, tile_width: int, tile_height: int, color: RGBA255, line_width: int) -> ShapeElementList:
    ...

