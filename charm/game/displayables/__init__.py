from typing import Protocol

from charm.game.displayables.countdown import Countdown
from charm.game.displayables.hp_bar import HPBar
from charm.game.displayables.lyric_animator import LyricAnimator
from charm.game.displayables.note_streak_display import NoteStreakDisplay
from charm.game.displayables.numeric_display import NumericDisplay
from charm.game.displayables.spotlight import Spotlight
from charm.game.displayables.timer import Timer

class Displayable(Protocol):
    def update(self, song_time: float) -> None:
        ...

    def draw(self) -> None:
        ...

__all__ = (
    "Displayable",
    "Countdown",
    "HPBar",
    "LyricAnimator",
    "NoteStreakDisplay",
    "NumericDisplay",
    "Spotlight",
    "Timer",
)