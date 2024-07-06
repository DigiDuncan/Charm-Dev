from charm.lib.components import Component
from charm.lib.generic.engine import Engine


class Display(Component):

    def __init__(self, engine: Engine):
        self._engine: Engine = engine

    def on_update(self, delta_time: float) -> None:
        return self.update(delta_time)

    def update(self, delta_time: float) -> None:
        pass

    def draw(self) -> None:
        return super().draw()
