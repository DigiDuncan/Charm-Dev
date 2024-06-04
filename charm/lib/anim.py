from dataclasses import dataclass
import math
from typing import Protocol

from charm.lib.utils import clamp, snap

class EasingFunction(Protocol):
    def __call__(self, minimum: float, maximum: float, p: float) -> float:
        """Eases a value between two values over an amount of time, smoothly.

        * `minimum: float`: the value returned by `p == 0`
        * `maximum: float`: the value returned by `p == 1`
        * `p: float`: percentage of progression, 0 to 1

        Returns a factor as float."""
        raise NotImplementedError


@dataclass
class LerpData:
    minimum: float
    maximum: float
    start_time: float
    end_time: float


def perc(start: float, end: float, curr: float) -> float:
    """Convert a number to its progress through the range start -> end, from 0 to 1.

    https://www.desmos.com/calculator/d2qdk3lceh"""
    if end - start <= 0:
        return 1 if curr >= start else 0
    duration = end - start
    p = (curr - start) / duration
    return clamp(0, p, 1)


def lerp(start: float, end: float, i: float) -> float:
    """Convert a number between 0 and 1 to be the progress within a range start -> end."""
    return start + (i * (end - start))


def bounce(n: float, m: float, bpm: float, x: float) -> float:
    """Create a bouncing motion between max(0, n) and m at bpm at time x."""
    return max(abs(math.sin(x * math.pi * (bpm / 60))) * m, n)


# All ease_ functions are two steps:
# manipulate p to redefine the curve
# lerp(min, max, p)

# TODO: Just add all the ones from easings.net. It'll be helpful to have the around.
# Might even be worth putting them in an "enum", EasingFunctions.


def ease_linear(minimum: float, maximum: float, p: float) -> float:
    """* `minimum: float`: the value returned by `p == 0`
       * `maximum: float`: the value returned by `p == 1`
       * `p: float`: percentage of progression, 0 to 1"""
    return lerp(minimum, maximum, p)


def ease_quadinout(minimum: float, maximum: float, p: float) -> float:
    """https://easings.net/#easeInOutQuad
       * `minimum: float`: the value returned by `p == 0`
       * `maximum: float`: the value returned by `p == 1`
       * `p: float`: percentage of progression, 0 to 1"""
    if p < 0.5:
        p2 = 2 * p * p
    else:
        p2 = 1 - math.pow(-2 * p + 2, 2) / 2
    return lerp(minimum, maximum, p2)


def ease_quartout(minimum: float, maximum: float, p: float) -> float:
    """https://easings.net/#easeOutQuart
       * `minimum: float`: the value returned by `p == 0`
       * `maximum: float`: the value returned by `p == 1`
       * `p: float`: percentage of progression, 0 to 1"""
    p2 = 1 - math.pow(1 - p, 4)
    return lerp(minimum, maximum, p2)


def ease_circout(minimum: float, maximum: float, p: float) -> float:
    """https://easings.net/#easeOutCirc
       * `minimum: float`: the value returned by `p == 0`
       * `maximum: float`: the value returned by `p == 1`
       * `p: float`: percentage of progression, 0 to 1"""
    p2 = math.sqrt(1 - math.pow(p - 1, 2))
    return lerp(minimum, maximum, p2)


def ease_expoout(minimum: float, maximum: float, p: float) -> float:
    """* `minimum: float`: the value returned by `p == 0`
       * `maximum: float`: the value returned by `p == 1`
       * `p: float`: percentage of progression, 0 to 1"""
    p2 = 1 - math.pow(2, -10 * p)
    return lerp(minimum, maximum, p2)


def ease_snap(minimum: float, maximum: float, p: float) -> float:
    """* `minimum: float`: the value returned by `p == 0`
       * `maximum: float`: the value returned by `p == 1`
       * `p: float`: percentage of progression, 0 to 1"""
    p2 = snap(p, 1)
    return lerp(minimum, maximum, p2)
