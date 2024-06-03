from __future__ import annotations
from functools import cache
from pathlib import Path
from typing import Any, Iterator, Protocol, TypeAlias, TypeVar
from collections.abc import Iterable
import importlib.resources as pkg_resources

import pyglet
import pyglet.image
import PIL.Image

from charm.lib.types import RGB, RGBA


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


SupportsRichComparison: TypeAlias = SupportsDunderLT[Any] | SupportsDunderGT[Any]


TT = TypeVar("TT", bound=SupportsRichComparison)


def clamp(minVal: TT, val: TT, maxVal: TT) -> TT:
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
        image = pyglet.image.load("unknown.png", file=f)
    return image


@cache
def img_from_path(path: Path) -> PIL.Image.Image:
    with open(path, 'b') as f:
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

def flatten(x: Iterable[Any] | Any) -> list[Any]:
    if isinstance(x, Iterable):
        return [a for i in x for a in flatten(i)]
    else:
        return [x]


T = TypeVar("T")

def findone(iterator: Iterator[T]) -> T | None:
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


def typewriter(s: str, cps: float, now: float, begin: float = 0) -> str:
    seconds = now - begin
    chars = int(max(0, (seconds * cps)))
    return s[:chars]
