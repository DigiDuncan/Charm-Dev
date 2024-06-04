from typing import Protocol, runtime_checkable


@runtime_checkable
class HasOnUpdate(Protocol):
    def on_update(self, delta_time: float) -> None:
        ...


@runtime_checkable
class HasDraw(Protocol):
    def draw(self) -> None:
        ...


@runtime_checkable
class HasOnResize(Protocol):
    def on_resize(self, width: int, height: int) -> None:
        ...


class ComponentManager:
    def __init__(self):
        self.has_on_update: list[HasOnUpdate] = []
        self.has_draw: list[HasDraw] = []
        self.has_on_resize: list[HasOnResize] = []

    def reset(self) -> None:
        self.has_on_update = []
        self.has_draw = []
        self.has_on_resize = []

    def register[T](self, component: T) -> T:
        if isinstance(component, HasOnUpdate):
            self.has_on_update.append(component)
        if isinstance(component, HasDraw):
            self.has_draw.append(component)
        if isinstance(component, HasOnResize):
            self.has_on_resize.append(component)
        return component

    def on_resize(self, width: int, height: int) -> None:
        for component in self.has_on_resize:
            component.on_resize(width, height)

    def on_update(self, delta_time: float) -> None:
        for component in self.has_on_update:
            component.on_update(delta_time)

    def on_draw(self) -> None:
        for component in self.has_draw:
            component.draw()
