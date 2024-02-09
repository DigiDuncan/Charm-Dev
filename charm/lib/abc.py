from abc import ABC, abstractmethod


class Drawable(ABC):

    @property
    @abstractmethod
    def center_x(self) -> float:
        ...

    @property
    @abstractmethod
    def center_y(self) -> float:
        ...

    @abstractmethod
    def update(self, delta_time: float) -> None:
        ...

    @abstractmethod
    def draw(self) -> None:
        ...
