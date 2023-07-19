from addict import Dict

class Settings(Dict):
    def __missing__(self, name):
        raise KeyError(name)

    def get_volume(self, mixer: str) -> float:
        match mixer:
            case "default" | "master":
                return self.volume.master
            case "music":
                return self.volume.master * self.volume.music
            case "sound":
                return self.volume.master * self.volume.sound
            case "menu_music":
                return self.volume.master * self.volume.menu_music
            case _:
                return self.volume.master


settings_dict = {
    "volume": {
        "master": 1.0,
        "music": 1.0,
        "menu_music": 1.0,
        "sound": 1.0
    },
    "resolution": {
        "width": 1280,
        "height": 720
    },
    "fps": 240
}

settings = Settings(settings_dict)
