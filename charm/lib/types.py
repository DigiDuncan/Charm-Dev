"""
These are meant for clarity ONLY.
They don't differentiate between different identical aliases.
They do no bounds checking.
It's just for readability in function signatures.
"""

from typing import Literal, Protocol


type Seconds = float
type Milliseconds = float
NEVER: Seconds = -float('inf')
FOREVER: Seconds = float('inf')

type RGB = tuple[int, int, int]
type RGBA = tuple[int, int, int, int]
type TuplePoint = tuple[int | float, int | float]

type Range4 = Literal[0, 1, 2, 3]
type Range8 = Literal[0, 1, 2, 3, 4, 5, 6, 7]

class Point:
    def __init__(self, point: TuplePoint):
        self._point = point

    @property
    def x(self) -> float:
        return self._point[0]

    @x.setter
    def x(self, val: float) -> None:
        self._point = (val, self._point[1])

    @property
    def y(self) -> float:
        return self._point[1]

    @y.setter
    def y(self, val: float) -> None:
        self._point = (self._point[0], val)

    @property
    def xy(self) -> tuple[float, float]:
        return self._point

    def move(self, x: float, y: float) -> None:
        self._point = (self._point[0] + x, self._point[1] + y)

    def __str__(self) -> str:
        return f"Point({self.x}, {self.y})"


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
