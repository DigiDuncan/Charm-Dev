from typing import Protocol

class Drawable(Protocol):
    @property
    def position(self) -> tuple[float, float]:
        ...

    @property
    def center_x(self) -> float:
        ...

    @property
    def center_y(self) -> float:
        ...

    def update(self, delta_time: float) -> None:
        ...

    def draw(self) -> None:
        ...
