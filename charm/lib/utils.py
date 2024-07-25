from __future__ import annotations
from typing import TYPE_CHECKING, Any, Protocol, TypeVar
if TYPE_CHECKING:
    from pathlib import Path
    from collections.abc import Iterator
    from charm.lib.generic.song import Metadata
    from charm.lib.types import RGB, RGBA


from functools import cache
from collections.abc import Iterable
from importlib.resources import files

from arcade import Texture
import pyglet.image
import PIL.Image

import charm.data.images


def int_or_str(i: Any) -> int | str:
    try:
        o = int(i)
    except ValueError:
        o = str(i)
    return o


# Stolen from pylance
_T_contra = TypeVar("_T_contra", contravariant=True)

class SupportsDunderLT(Protocol[_T_contra]):
    def __lt__(self, other: _T_contra, /) -> bool:
        ...

class SupportsDunderGT(Protocol[_T_contra]):
    def __gt__(self, other: _T_contra, /) -> bool:
        ...


type SupportsRichComparison = SupportsDunderLT[Any] | SupportsDunderGT[Any]


TT = TypeVar("TT", bound=SupportsRichComparison)


def clamp(min_val: TT, val: TT, mav_val: TT) -> TT:
    """Clamp a `val` to be no lower than `minVal`, and no higher than `maxVal`."""
    return max(min_val, min(mav_val, val))


@cache
def pyglet_img_from_path(path: Path) -> pyglet.image.AbstractImage:
    with path.open("rb") as f:
        image = pyglet.image.load("unknown.png", file=f)
    return image


@cache
def img_from_path(path: Path) -> PIL.Image.Image:
    with path.open('rb') as f:
        image = PIL.Image.open(f)
        image.load()
    return image


def map_range(x: float, n1: float, m1: float, n2: float = -1, m2: float = 1) -> float:
    """Scale a float `x` that is currently somewhere between `n1` and `m1` to now be in an
    equivalent position between `n2` and `m2`."""
    # Make the range start at 0.
    old_max = m1 - n1
    old_x = x - n1
    percentage = old_x / old_max

    new_max = m2 - n2
    new_pos = new_max * percentage
    ans = new_pos + n2
    return ans

# Stinky shenanigans that nuitka (and Dragon) doesn't like
# type Flatable[T] = T | Iterable[Flatable[T]]
# 
# def flatten[T: Any](item: Flatable[T]) -> list[T]:
#     if not isinstance(item, Iterable):
#         return [item]
#     return [newitem for subitem in item for newitem in flatten(subitem)]
# 
# 
# def next_or_none[T](iterator: Iterator[T]) -> T | None:
#     try:
#         val = next(iterator)
#     except StopIteration:
#         val = None
#     return val


def color_with_alpha(color: RGB | RGBA, alpha: int) -> RGBA:
    return color[:3] + (alpha,)


def nuke_smart_quotes(s: str) -> str:
    return s.replace("‘", "'").replace("’", "'").replace("＇", "'").replace("“", '"').replace("”", '"').replace("＂", '"')


def pt_to_px(pt: int) -> int:
    return round(pt * (4 / 3))


def px_to_pt(px: int) -> int:
    return round(px // (4 / 3))


def snap(n: float, increments: int) -> float:
    return round(increments * n) / increments


def typewriter(s: str, cps: float, now: float, begin: float = 0) -> str:
    seconds = now - begin
    chars = int(max(0, (seconds * cps)))
    return s[:chars]


def get_album_art(metadata: Metadata, size: int = 200) -> Texture:
    """Get an album art Texture from a song metadata."""
    # Iterate through frankly too many possible paths for the album art location.
    art_path = None
    # Clone Hero-style (also probably the recommended format.)
    art_paths = [
        metadata.path / "album.jpg",
        metadata.path / "album.png",
        metadata.path / "album.gif"
    ]
    # Stepmania-style
    art_paths.extend(metadata.path.glob("*jacket.png"))
    art_paths.extend(metadata.path.glob("*jacket.gif"))
    art_paths.extend(metadata.path.glob("*jacket.jpg"))
    for p in art_paths:
        if p.is_file():
            art_path = p
            break

    if art_path is not None:
        album_art_img = PIL.Image.open(art_path)
    else:
        # We *still* didn't find one? Fine.
        album_art_img = img_from_path(files(charm.data.images) / "no_image_found.png")

    # Resize to requested size
    album_art_img = album_art_img.convert("RGBA")
    if (album_art_img.width != size or album_art_img.height != size):
        album_art_img = album_art_img.resize((size, size))

    album_art = Texture(album_art_img)
    return album_art
