from __future__ import annotations

from enum import StrEnum
from charm.refactor.generic.chart import Chart, Note

class HeroNoteType(StrEnum):
    STRUM = "strum"
    HOPO = "hopo"
    TAP = "tap"

class HeroNote(Note[HeroNoteType]):
    pass

class HeroChart(Chart[HeroNote]):
    pass
