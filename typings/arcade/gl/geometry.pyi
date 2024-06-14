"""
This type stub file was generated by pyright.
"""

from typing import Tuple
from arcade.gl.vertex_array import Geometry

"""
A module providing commonly used geometry
"""
def quad_2d_fs() -> Geometry:
    """Creates a screen aligned quad using normalized device coordinates"""
    ...

def quad_2d(size: Tuple[float, float] = ..., pos: Tuple[float, float] = ...) -> Geometry:
    """
    Creates 2D quad Geometry using 2 triangle strip with texture coordinates.

    :param size: width and height
    :param pos: Center position x and y
    """
    ...

def screen_rectangle(bottom_left_x: float, bottom_left_y: float, width: float, height: float) -> Geometry:
    """
    Creates screen rectangle using 2 triangle strip with texture coordinates.

    :param bottom_left_x: Bottom left x position
    :param bottom_left_y: Bottom left y position
    :param width: Width of the rectangle
    :param height: Height of the rectangle
    """
    ...

def cube(size: Tuple[float, float, float] = ..., center: Tuple[float, float, float] = ...) -> Geometry:
    """Creates a cube with normals and texture coordinates.

    :param size: size of the cube as a 3-component tuple
    :param center: center of the cube as a 3-component tuple
    :returns: A cube
    """
    ...

def sphere(radius=..., sectors=..., rings=..., normals=..., uvs=...) -> Geometry:
    """
    Creates a 3D sphere.

    :param radius: Radius or the sphere
    :param rings: number or horizontal rings
    :param sectors: number of vertical segments
    :param normals: Include normals in the VAO
    :param uvs: Include texture coordinates in the VAO
    :return: A geometry object
    """
    ...

