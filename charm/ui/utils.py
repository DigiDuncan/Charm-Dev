from hashlib import sha1
import io
import os
from pathlib import Path
import PIL.Image
from arcade import Texture
import requests
from charm.lib.generic.song import Metadata


def get_album_art(metadata: Metadata) -> Texture:
    # Make a real hash, probably on Song.
    key = sha1((str(metadata.title) + str(metadata.artist) + str(metadata.album)).encode()).hexdigest()

    art_path = None
    art_paths = [Path(metadata.path / "album.jpg"),
                 Path(metadata.path / "album.png"),
                 Path(metadata.path / "album.gif")]
    art_paths.extend(metadata.path.glob("*jacket.png"))
    art_paths.extend(metadata.path.glob("*jacket.gif"))
    art_paths.extend(metadata.path.glob("*jacket.jpg"))
    for p in art_paths:
        if p.is_file():
            art_path = p
            break
    if art_path is None:
        # Make sure this directory, like, exists?
        if not Path("./albums").exists():
            os.mkdir("./albums")
        try:
            album_art_img = PIL.Image.open(f"./albums/album_{key}.png")
        except FileNotFoundError:
            album_art = io.BytesIO(requests.get("https://picsum.photos/200.jpg").content)
            album_art_img = PIL.Image.open(album_art)
            with open(f"./albums/album_{key}.png", "wb+") as p:
                album_art_img.save(p)
    else:
        album_art_img = PIL.Image.open(art_path)
    album_art_img = album_art_img.convert("RGBA")
    if (album_art_img.width != 200 or album_art_img.height != 200):
        album_art_img = album_art_img.resize((200, 200))

    album_art = Texture(album_art_img)
    return album_art
