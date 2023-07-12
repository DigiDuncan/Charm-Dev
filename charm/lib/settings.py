from addict import Dict

class Settings(Dict):
    def __missing__(self, name):
        raise KeyError(name)


settings_dict = {
    "volume": {
        "master": 1.0,
        "music": 1.0,
        "sound": 1.0
    },
    "resolution": {
        "width": 1280,
        "height": 720
    },
    "fps": 240
}

settings = Settings(settings_dict)

def get_volume(mixer: str):
    match mixer:
        case "default" | "master":
            return settings.volume.master
        case "music":
            return settings.volume.master * settings.volume.music
        case "sound":
            return settings.volume.master * settings.volume.sound
        case _:
            return settings.volume.master
