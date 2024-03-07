from typing import Optional
from nindex import Index
from charm.lib.anim import EasingFunction, ease_linear
from charm.lib.generic.song import BPMChangeEvent
from charm.lib.utils import NormalizedFloat


class BPMAnimator:
    def __init__(self, events: list[BPMChangeEvent], func: Optional[EasingFunction] = None, t = 0.0) -> None:
        self.func = func if func else ease_linear
        self.t = t

        self.events_by_time = Index(events, "time")

    def update(self, delta_time: float):
        self.t += delta_time

    def reset(self, events: list[BPMChangeEvent]):
        self.t = 0
        self.events_by_time = Index(events, "time")

    @property
    def current_bpm(self) -> float:
        return self.events_by_time.lteq(self.t).new_bpm

    @property
    def magnitude(self) -> NormalizedFloat:
        """https://www.desmos.com/calculator/jwnfdhtsny"""
        return abs(((self.t % (60 / self.current_bpm)) * (self.current_bpm / 60)) - 0.5) * 2

    @property
    def factor(self) -> NormalizedFloat:
        return self.func(0, 1, 0, 1, self.magnitude)
