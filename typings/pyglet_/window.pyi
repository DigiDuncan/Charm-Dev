import pyglet.image

class Window:
    def set_icon(self, *images: pyglet.image.AbstractImage) -> None:
        ...

    @property
    def fullscreen(self) -> bool:
        ...

    @property
    def width(self) -> int:
        ...

    @property
    def height(self) -> int:
        ...
