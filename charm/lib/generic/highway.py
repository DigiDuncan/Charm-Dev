import arcade
from arcade import Camera2D

from charm.lib.generic.song import Chart


class Highway:
    def __init__(self, chart: Chart, pos: tuple[int, int], size: tuple[int, int] = None, gap: int = 5, downscroll = False):
        """A time-based display of current and upcoming notes to be hit by the player."""
        self.chart = chart
        self.notes = self.chart.notes

        self._pos = pos
        self.gap = gap
        self.downscroll = downscroll
        self.viewport: float = 1
        self.window = arcade.get_window()
        self.size = size if size is not None else (self.window.width // 3, self.window.height)

        self.static_camera = Camera2D()
        self.highway_camera = Camera2D()
        self.song_time: float = 0

    @property
    def pos(self) -> tuple[int, int]:
        return self._pos

    @pos.setter
    def pos(self, p: tuple[int, int]):
        self._pos = p

    @property
    def px_per_s(self):
        return self.h / self.viewport

    @property
    def x(self) -> int:
        return self.pos[0]

    @x.setter
    def x(self, i: int):
        self.pos = (i, self.pos[1])

    @property
    def y(self) -> int:
        return self.pos[1]

    @y.setter
    def y(self, i: int):
        self.pos = (self.pos[0], i)

    @property
    def w(self) -> int:
        return self.size[0]

    @w.setter
    def w(self, i: int):
        self.size = (i, self.size[1])

    @property
    def h(self) -> int:
        return self.size[1]

    @h.setter
    def h(self, i: int):
        self.size = (self.size[0], i)

    @property
    def note_size(self) -> int:
        return (self.w // self.chart.lanes) - self.gap

    @property
    def strikeline_y(self):
        if self.downscroll:
            return 89  # 64 + 25
        return self.h - 25

    @property
    def visible_notes(self):
        return [n for n in self.notes if self.song_time - self.viewport < n.time <= self.song_time + self.viewport]

    def apos(self, rpos: tuple[int, int]) -> tuple[int, int]:
        return (rpos[0] + self.pos[0], rpos[1] + self.pos[1])

    def lane_x(self, lane_num):
        return (self.note_size + self.gap) * lane_num + self.x

    def note_y(self, at: float):
        rt = at - self.song_time
        if self.downscroll:
            return (self.px_per_s * rt) + self.strikeline_y
        return (-self.px_per_s * rt) + self.strikeline_y + self.y

    def update(self, song_time):
        self.song_time = song_time

    def draw(self):
        raise NotImplementedError
