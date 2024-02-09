from pathlib import Path
from typing import Union

from pyglet import media
from pyglet.media.codecs.pyogg import PyOggDecoder
from arcade import Sound
from arcade.resources import resolve_resource_path

pyogg_decoder = PyOggDecoder()


class OGGSound(Sound):
    """This class represents an OGG sound you can play."""
    def __init__(self, file_name: Union[str, Path], streaming: bool = False):
        self.file_name: str = ""
        file_name = resolve_resource_path(file_name)

        if not Path(file_name).is_file():
            raise FileNotFoundError(f"The sound file '{file_name}' is not a file or can't be read.")

        self.file_name = str(file_name)

        self.source: Union[media.StaticSource, media.StreamingSource] = media.load(
            self.file_name, streaming=streaming, decoder=pyogg_decoder)

        self.min_distance = 100000000  # setting the players to this allows for 2D panning with 3D audio
