from typing import Self

from importlib.resources import files, as_file

import arcade
from arcade import Sound

import charm.data.audio
from charm.lib.settings import MixerNames, settings


class Sfx:
    def __init__(self, sound: Sound):
        self.sound: Sound = sound
        self.mixer: MixerNames = "sound"

    def play(self) -> None:
        arcade.play_sound(self.sound, volume = settings.get_volume(self.mixer))

    @classmethod
    def load(cls, resource: str) -> Self:
        with as_file(files(charm.data.audio) / resource) as f:
            sound = Sound(f)
        return cls(sound)


class SfxManager:
    def __init__(self):
        self.back = Sfx.load("sfx-back.wav")
        self.select = Sfx.load("sfx-select.wav")
        self.valid = Sfx.load("sfx-valid.wav")
        self.error = Sfx.load("error-error.wav")
        self.warning = Sfx.load("error-warning.wav")
        self.info = Sfx.load("error-info.wav")
