from typing import Self

from importlib.resources import files, as_file

import arcade
from arcade import Sound

import charm.data.audio
from charm.core.settings import settings, Mixer


class SFX:
    def __init__(self, sound: Sound):
        self.sound: Sound = sound
        self.mixer: Mixer = Mixer.sfx

    def play(self) -> None:
        arcade.play_sound(self.sound, volume = settings.get_volume(self.mixer))

    @classmethod
    def load(cls, resource: str) -> Self:
        with as_file(files(charm.data.audio) / resource) as f:
            sound = Sound(f)
        return cls(sound)


class SFXManager:
    def __init__(self):
        self.back = SFX.load("sfx-back.wav")
        self.select = SFX.load("sfx-select.wav")
        self.valid = SFX.load("sfx-valid.wav")
        self.error = SFX.load("error-error.wav")
        self.warning = SFX.load("error-warning.wav")
        self.info = SFX.load("error-info.wav")
