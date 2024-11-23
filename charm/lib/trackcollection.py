import logging
from typing import Self
from pathlib import Path

from arcade import Sound
from arcade.clock import GLOBAL_CLOCK
from charm.lib.oggsound import OGGSound

from charm.core.settings import MixerNames, settings

logger = logging.getLogger("charm")

class TrackCollection:
    def __init__(self, sounds: list[Sound], mixer: MixerNames = "music"):
        self.start_time: float = -1.0
        self.delay: float = 0.0
        self.mixer = mixer
        self.tracks = [s.play(volume = settings.get_volume(self.mixer)) for s in sounds]
        self.pause()
        self.seek(0.0)

    @classmethod
    def from_path(cls, path: Path) -> Self:
        track_files = [f for f in path.iterdir() if f.is_file() and f.suffix in {".ogg", ".mp3", ".wav"}]
        tracks = [OGGSound(track) if track.suffix == '.ogg' else Sound(track) for track in track_files]
        return cls(tracks)

    @property
    def time(self) -> float:
        if not self.tracks:
            return 0.0
        if self.start_time >= 0 and not self.playing and GLOBAL_CLOCK.time_since(self.start_time) <= self.delay:
            return GLOBAL_CLOCK.time_since(self.start_time) - self.delay
        return self.tracks[0].time

    @property
    def duration(self) -> float:
        if not self.tracks:
            return 0.0
        return max([t.source.duration if t.source else 0 for t in self.tracks])

    @property
    def playing(self) -> bool:
        if not self.tracks:
            return False
        return self.tracks[0].playing

    @property
    def volume(self) -> float:
        if not self.tracks:
            return 1.0
        return self.tracks[0].volume

    @volume.setter
    def volume(self, v: float) -> None:
        for t in self.tracks:
            t.volume = v

    def seek(self, time: float) -> None:
        playing = self.playing
        if playing:
            self.pause()
        for t in self.tracks:
            t.seek(time)
        if playing:
            self.play()

    def start(self, delay: float = 0.0) -> None:
        self.pause()
        self.seek(0)
        self.delay = delay
        self.start_time = GLOBAL_CLOCK.time

    def validate_playing(self) -> None:
        if self.start_time < 0:
            return

        if not self.playing and GLOBAL_CLOCK.time_since(self.start_time) >= self.delay:
            self.seek(GLOBAL_CLOCK.time_since(self.start_time) - self.delay)
            self.start_time = -1.0
            self.delay = 0.0
            self.play()

    def play(self) -> None:
        self.sync()
        for t in self.tracks:
            t.play()

    def pause(self) -> None:
        for t in self.tracks:
            t.pause()

    def close(self) -> None:
        self.pause()
        for t in self.tracks:
            t.delete()
        self.tracks = []

    @property
    def loaded(self) -> bool:
        return bool(self.tracks)

    def sync(self) -> None:
        self.log_sync()
        maxtime = max(t.time for t in self.tracks)
        self.seek(maxtime)

    def log_sync(self) -> None:
        mintime = min(t.time for t in self.tracks)
        maxtime = max(t.time for t in self.tracks)
        sync_diff = (maxtime - mintime) * 1000
        logger.debug(f"Track sync: {sync_diff:.0f}ms")
        if sync_diff > 10:
            logger.warning("Tracks are out of sync by more than 10ms!")

