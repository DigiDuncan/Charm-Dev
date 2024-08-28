from typing import Literal
from dataclasses import dataclass

MixerNames = Literal["default", "master", "music", "sound", "menu_music"]

@dataclass
class Volume:
    master = 0.4
    music = 1.0
    menu_music = 1.0
    sound = 1.0


class Settings:
    def __init__(self):
        self.volume = Volume()
        self.resolution = (1280, 720)
        self.fps = 10000

    def get_volume(self, mixer: MixerNames) -> float:
        match mixer:
            case "default" | "master":
                return self.volume.master
            case "music":
                return self.volume.master * self.volume.music
            case "sound":
                return self.volume.master * self.volume.sound
            case "menu_music":
                return self.volume.master * self.volume.menu_music


settings: Settings = Settings()
