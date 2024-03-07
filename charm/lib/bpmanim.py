from typing import Optional
from nindex import Index
from charm.lib.anim import EasingFunction, ease_linear
from charm.lib.generic.song import BPMChangeEvent
from charm.lib.utils import NormalizedFloat


class BPMAnimator:
    def __init__(self, events: list[BPMChangeEvent], func: Optional[EasingFunction] = None, t = 0.0) -> None:
        """An animator driven off BPMChangeEvents, in order to sync animations with a playing music track.

        - `events: list[BPMChangeEvent]`: A synctrack for the currently playing song.
        - `func: Optional[EasingFunction]`: An easing function to smooth the animation. Defaults to linear.
        - `t: float = 0.0`: Sets the current time to `t` if starting part-way through a song."""
        self.func = func if func else ease_linear
        self.t = t
        self._t_offset = 0

        self.events_by_time = Index(events, "time")

    def update(self, *, time: float = None):
        """Syncs the animator to the current song time."""
        old_bpm = self.current_bpm
        self.t = time
        if self.current_bpm != old_bpm:
            self._t_offset = self.t

    def reset(self, events: list[BPMChangeEvent]):
        """Reuse this animator with a new set of BPMChangeEvents, usually to change what song is playing."""
        self.t = 0
        self._t_offset = 0
        self.events_by_time = Index(events, "time")

    @property
    def current_bpm(self) -> float:
        """The current BPM, as a float."""
        return self.events_by_time.lteq(self.t).new_bpm

    @property
    def magnitude(self) -> NormalizedFloat:
        """The current magnitude. 1 on beats, 0 between beats, lerps between.

        https://www.desmos.com/calculator/jwnfdhtsny"""
        return abs(((self.current_bpm * (self.t - self._t_offset)) / 60 % 1) - 0.5) * 2

    @property
    def factor(self) -> NormalizedFloat:
        """Returns the magnitude, smoothed with the easing function assigned to this animator."""
        return self.func(0, 1, 0, 1, self.magnitude)
