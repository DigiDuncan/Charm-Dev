from hashlib import sha1
from pathlib import Path

import PIL.Image
from arcade import Texture

import charm.data.images
from charm.lib.generic.song import Metadata
from charm.lib.utils import img_from_resource


def get_album_art(metadata: Metadata, size = 200) -> Texture:
    # Iterate through frankly too many possible paths for the album art location.
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
        # We *still* didn't find one? Fine.
        # Make sure this directory, like, exists?
        album_art_img = img_from_resource(charm.data.images, "no_image_found.png")
    else:
        album_art_img = PIL.Image.open(art_path)

    # Resize to requested size
    album_art_img = album_art_img.convert("RGBA")
    if (album_art_img.width != size or album_art_img.height != size):
        album_art_img = album_art_img.resize((size, size))

    album_art = Texture(album_art_img)
    return album_art
