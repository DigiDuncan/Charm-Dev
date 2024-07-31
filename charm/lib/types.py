"""
These are meant for clarity ONLY.
They don't differentiate between different identical aliases.
They do no bounds checking.
It's just for readability in function signatures.
"""

from typing import Literal


Seconds = float
Milliseconds = float

RGB = tuple[int, int, int]
RGBA = tuple[int, int, int, int]
TuplePoint = tuple[int | float, int | float]

Range4 = Literal[0, 1, 2, 3]
Range8 = Literal[0, 1, 2, 3, 4, 5, 6, 7]

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

    def move(self, x: float, y: float) -> None:
        self._point = (self._point[0] + x, self._point[1] + y)

    def __str__(self) -> str:
        return f"Point({self.x}, {self.y})"
