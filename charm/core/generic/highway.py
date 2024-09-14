from typing import Generic, TypeVar
import arcade
from arcade import Camera2D
from arcade.camera import Projector

from charm.lib.types import Seconds

from .chart import BaseChart, BaseNote
from .engine import BaseEngine


type BaseHighway = Highway[BaseChart, BaseNote, BaseEngine]

C = TypeVar("C", bound=BaseChart, covariant=True)
N = TypeVar("N", bound=BaseNote, covariant=True)
E = TypeVar("E", bound=BaseEngine, covariant=True)


class Highway(Generic[C, N, E]):
    def __init__(self, chart: C, engine: E, pos: tuple[int, int], size: tuple[int, int] | None = None, gap: int = 5, viewport: float = 1.0, *, downscroll: bool = False, static_camera: Projector = None, highway_camera: Projector = None):
        """A time-based display of current and upcoming notes to be hit by the player."""
        self.chart = chart
        self.engine = engine
        self.notes = self.chart.notes

        self._pos = pos
        self.gap = gap
        self.downscroll = downscroll
        self.viewport: float = viewport
        self.window = arcade.get_window()  # ???: This can't be a good idea, right? ~Digi - Yeah, but its how arcade is designed ~Dragon
        self.size = size if size is not None else (self.window.width // 3, self.window.height)

        # !: This isn't a valid assumption for the hero/rock gamemode.
        self.static_camera: Projector = static_camera or Camera2D()
        self.highway_camera: Projector = highway_camera or Camera2D()
        self.song_time: float = 0

    @property
    def pos(self) -> tuple[int, int]:
        return self._pos

    @pos.setter
    def pos(self, p: tuple[int, int]) -> None:
        self._pos = p

    @property
    def px_per_s(self) -> float:
        return float('inf') if not self.viewport else self.h / self.viewport

    @property
    def x(self) -> int:
        return self.pos[0]

    @x.setter
    def x(self, i: int) -> None:
        self.pos = (i, self.pos[1])

    @property
    def y(self) -> int:
        return self.pos[1]

    @y.setter
    def y(self, i: int) -> None:
        self.pos = (self.pos[0], i)

    @property
    def w(self) -> int:
        return self.size[0]

    @w.setter
    def w(self, i: int) -> None:
        self.size = (i, self.size[1])

    @property
    def h(self) -> int:
        return self.size[1]

    @h.setter
    def h(self, i: int) -> None:
        self.size = (self.size[0], i)

    @property
    def note_size(self) -> int:
        raise NotImplementedError

    @property
    def strikeline_y(self) -> int:
        if self.downscroll:
            return 89  # 64 + 25
        return self.h - 25

    @property
    def visible_notes(self) -> list[N]:
        return [n for n in self.notes if self.song_time - self.viewport < n.time <= self.song_time + self.viewport]

    def apos(self, rpos: tuple[int, int]) -> tuple[int, int]:
        return (rpos[0] + self.pos[0], rpos[1] + self.pos[1])

    def lane_x(self, lane_num: int) -> float:
        return (self.note_size + self.gap) * lane_num + self.x

    def note_y(self, at: float) -> float:
        rt = at - self.song_time
        if self.downscroll:
            return (self.px_per_s * rt) + self.strikeline_y
        return (-self.px_per_s * rt) + self.strikeline_y + self.y

    def update(self, song_time: Seconds) -> None:
        self.song_time = song_time

    def draw(self) -> None:
        raise NotImplementedError
