# ! Deprecated

class Component:
    def on_update(self, delta_time: float) -> None:
        return

    def on_resize(self, width: int, height: int) -> None:
        return

    def draw(self) -> None:
        return

class ComponentManager:
    def __init__(self):
        self.components: list[Component] = []

    def reset(self) -> None:
        self.components = []

    def register[T: Component](self, component: T) -> T:
        self.components.append(component)
        return component

    def on_update(self, delta_time: float) -> None:
        for component in self.components:
            component.on_update(delta_time)

    def on_resize(self, width: int, height: int) -> None:
        for component in self.components:
            component.on_resize(width, height)

    def draw(self) -> None:
        for component in self.components:
            component.draw()

