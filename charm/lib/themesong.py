from __future__ import annotations

from importlib.resources import files, as_file

from arcade import Sound

from charm.lib.anim import ease_expoout
from charm.lib.bpmanim import BPMAnimator
from charm.lib.errors import CharmError
import charm.data.audio

from charm.core.generic import BPMChangeEvent


class ThemeSong:
    def __init__(self) -> None:
        with as_file(files(charm.data.audio) / "song.mp3") as f:
            song = Sound(f)
        try:
            self.player = song.play(volume=0, loop=True)
        except Exception as err:
            raise CharmError(
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
