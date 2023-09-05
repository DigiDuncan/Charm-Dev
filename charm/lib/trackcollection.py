import logging

import arcade
import pyglet.media as media

from charm.lib.settings import settings

logger = logging.getLogger("charm")

class TrackCollection:
    def __init__(self, sounds: arcade.Sound, mixer = "music"):
        self.mixer = mixer
        self.tracks: list[media.Player] = [s.play(volume = settings.get_volume(self.mixer)) for s in sounds]
        self.pause()
        self.seek(0)

    @property
    def time(self) -> float:
        return self.tracks[0].time

    @property
    def duration(self) -> float:
        return max([t.source.duration if t.source else 0 for t in self.tracks])

    @property
    def playing(self) -> bool:
        return self.tracks[0].playing

    @property
    def volume(self) -> float:
        return self.tracks[0].volume

    @volume.setter
    def volume(self, v: float):
        for t in self.tracks:
            t.volume = v

    def seek(self, time):
        playing = self.playing
        if playing:
            self.pause()
        for t in self.tracks:
            t.seek(time)
        if playing:
            self.play()

    def play(self):
        self.sync()
        for t in self.tracks:
            t.play()

    def pause(self):
        for t in self.tracks:
            t.pause()

    def close(self):
        self.pause()
        for t in self.tracks:
            t.delete()
        self.tracks = []

    @property
    def loaded(self) -> bool:
        return bool(self.tracks)

    def sync(self):
        self.log_sync()
        maxtime = max(t.time for t in self.tracks)
        self.seek(maxtime)

    def log_sync(self):
        mintime = min(t.time for t in self.tracks)
        maxtime = max(t.time for t in self.tracks)
        sync_diff = (maxtime - mintime) * 1000
        logger.debug(f"Track sync: {sync_diff:.0f}ms")
        if sync_diff > 10:
            logger.warning("Tracks are out of sync by more than 10ms!")
