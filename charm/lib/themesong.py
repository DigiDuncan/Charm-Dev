from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyglet.media import Player

from importlib.resources import files, as_file

import arcade

from charm.lib.anim import ease_expoout
from charm.lib.bpmanim import BPMAnimator
from charm.lib.errors import CharmException
from charm.lib.generic.song import BPMChangeEvent
import charm.data.audio

class ThemeSong:
    def __init__(self) -> None:
        with as_file(files(charm.data.audio) / "song.mp3") as f:
            song = arcade.Sound(f)
        try:
            self.player: Player = song.play(volume=0, loop=True)
        except Exception as err:
            raise CharmException(
                title="Song Failed",
                message="Failed to load theme song"
            ) from err
        bpm_events = [BPMChangeEvent(0, 120), BPMChangeEvent(3, 220)]
        self.beat_animator = BPMAnimator(bpm_events, ease_expoout)

    def on_update(self, delta_time: float) -> None:
        self.beat_animator.update(self.time)

    @property
    def beat_factor(self) -> float:
        return self.beat_animator.factor

    @property
    def time(self) -> float:
        return self.player.time

    @property
    def volume(self) -> float:
        return self.player.volume # type: ignore

    @volume.setter
    def volume(self, value: float) -> None:
        self.player.volume = value # type: ignore

    def seek(self, value: float) -> None:
        self.player.seek(value)

    @property
    def current_bpm(self) -> float:
        return self.beat_animator.current_bpm
