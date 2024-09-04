from collections.abc import Generator
from typing import Any

from charm.refactor.generic.chart import Chart
from charm.refactor.generic.sprite import NoteSprite
from charm.refactor.generic.engine import Engine
from charm.refactor.generic.highway import Highway
from charm.refactor.charts.taiko import TaikoChart, TaikoNote
from charm.lib.pool import SpritePool


class TaikoHighway(Highway):

    def __init__(self, chart: Chart, engine: Engine, pos: tuple[int, int], size: tuple[int, int] = None, gap: int = 5, viewport: float = 1):
        super().__init__(chart, engine, pos, size, gap, viewport)
        self.color = (0, 0, 0, 128)  # TODO: eventually this will be a scrolling image.

        # Generators are great for ease, but it means we can't really 'scrub' backwards through the song
        # So this is a patch job at best.
        self._note_generator: Generator[TaikoNote, Any, None] = (note for note in self.notes) # type: ignore[]
        self._note_pool: SpritePool[NoteSprite] = SpritePool([NoteSprite(x=-1000.0, y=-1000.0) for _ in range(1000)])
        self._next_note: TaikoNote | None = next(self._note_generator, None)


    @property
    def horizontal_viewport(self) -> float:
        return self.viewport * (self.window.width / self.window.height)
