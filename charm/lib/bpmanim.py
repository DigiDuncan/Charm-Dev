from typing import Optional
from nindex import Index
from charm.lib.anim import EasingFunction, ease_linear
from charm.lib.generic.song import BPMChangeEvent
from charm.lib.utils import NormalizedFloat


class BPMAnimator:
    def __init__(self, events: list[BPMChangeEvent], func: Optional[EasingFunction] = None, t = 0.0) -> None:
        self.func = func if func else ease_linear
        self.t = t
        self._t_offset = 0

        self.events_by_time = Index(events, "time")

    def update(self, *, time: float = None):
        old_bpm = self.current_bpm
        self.t = time
        if self.current_bpm != old_bpm:
            self._t_offset = self.t

    def reset(self, events: list[BPMChangeEvent]):
        self.t = 0
        self._t_offset = 0
        self.events_by_time = Index(events, "time")

    @property
    def current_bpm(self) -> float:
        return self.events_by_time.lteq(self.t).new_bpm

    @property
    def magnitude(self) -> NormalizedFloat:
        """https://www.desmos.com/calculator/jwnfdhtsny"""
        return abs(((self.current_bpm * (self.t - self._t_offset)) / 60 % 1) - 0.5) * 2

    @property
    def factor(self) -> NormalizedFloat:
        return self.func(0, 1, 0, 1, self.magnitude)
