from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from charm.refactor.generic.chart import Chart, Note

Ticks = int

class HeroNoteType(StrEnum):
    STRUM = "strum"
    HOPO = "hopo"
    TAP = "tap"

@dataclass
class HeroNote(Note[HeroNoteType]):
    tick: int | None = None
    tick_length: Ticks | None = None

class HeroChart(Chart[HeroNote]):
    pass
