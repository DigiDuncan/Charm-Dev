from __future__ import annotations

from typing import Any, BinaryIO, Literal

from pyglet.image.codecs import ImageEncoder, ImageDecoder
GL_TEXTURE_2D = Literal[3553]

class ImageData:
    ...


class Texture:
    ...


class AbstractImage:
    anchor_x: int
    anchor_y: int

    def __init__(self, width: int, height: int) -> None:
        ...

    def __repr__(self) -> str:
        ...

    def get_image_data(self) -> ImageData:
        ...

    def get_texture(self, rectangle: bool = False) -> Texture:
        ...

    def get_mipmapped_texture(self) -> Texture:
        ...

    def get_region(self, x: int, y: int, width: int, height: int) -> AbstractImage:
        ...

    def save(self, filename: str | None = None, file: BinaryIO | None = None, encoder: ImageEncoder | None = None) -> None:
        ...

    def blit(self, x: int, y: int, z: int = 0) -> None:
        ...

    def blit_into(self, source: AbstractImage, x: int, y: int, z: int) -> None:
        ...

    def blit_to_texture(self, target: Any, level: int, x: int, y: int, z: int = 0) -> None:
        ...


def load(filename: str, file: BinaryIO | None = None, decoder: ImageDecoder | None = None) -> AbstractImage:
    ...
