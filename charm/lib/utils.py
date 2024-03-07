from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Annotated, Any
import collections
import importlib.resources as pkg_resources

import pyglet
from pyglet.image import ImageData
import PIL.Image

RGB = tuple[int, int, int]
RGBA = tuple[int, int, int, int]

@dataclass
class ValueRange:
    lo: int
    hi: int


NormalizedFloat = Annotated[float, ValueRange(0.0, 1.0)]


def int_or_str(i: Any) -> int | str:
    try:
        o = int(i)
    except ValueError:
        o = str(i)
    return o


def clamp(minVal, val, maxVal):
    """Clamp a `val` to be no lower than `minVal`, and no higher than `maxVal`."""
    return max(minVal, min(maxVal, val))


@cache
def img_from_resource(package: pkg_resources.Package, resource: pkg_resources.Resource) -> PIL.Image.Image:
    with pkg_resources.open_binary(package, resource) as f:
        image = PIL.Image.open(f)
        image.load()
    return image


@cache
def pyglet_img_from_resource(package: pkg_resources.Package, resource: pkg_resources.Resource) -> pyglet.image.AbstractImage:
    with pkg_resources.open_binary(package, resource) as f:
        image: ImageData = pyglet.image.load("unknown.png", file=f)
    return image


@cache
def img_from_path(path: Path) -> PIL.Image.Image:
    with open(path) as f:
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


def flatten(x):
    if isinstance(x, collections.Iterable):
        return [a for i in x for a in flatten(i)]
    else:
        return [x]


def findone(iterator):
    try:
        val = next(iterator)
    except StopIteration:
        val = None
    return val


def color_with_alpha(color: RGB | RGBA, alpha: int):
    if len(color) == 3:
        return color + (alpha,)
    else:
        return color[:3] + (alpha,)


def nuke_smart_quotes(s: str) -> str:
    return s.replace("‘", "'").replace("’", "'").replace("＇", "'").replace("“", '"').replace("”", '"').replace("＂", '"')


def pt_to_px(pt: int) -> int:
    return round(pt * (4 / 3))


def px_to_pt(px: int) -> int:
    return round(px // (4 / 3))


def snap(n: float, increments: int) -> float:
    return round(increments * n) / increments
