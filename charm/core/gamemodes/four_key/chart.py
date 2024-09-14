from __future__ import annotations

from enum import StrEnum

from charm.lib.types import Seconds

from charm.core.generic import Chart, Note


class FourKeyNoteType(StrEnum):
    NORMAL = "normal"
    BOMB = "bomb"
    DEATH = "death"
    HEAL = "heal"
    CAUTION = "caution"
    STRIKELINE = "strikeline"
    SUSTAIN = "sustain"  # FNF specific and maybe going away one day


class FourKeyNote(Note["FourKeyChart", FourKeyNoteType]):
    def __init__(self, chart: FourKeyChart, time: Seconds, lane: int, length: Seconds = 0, type: FourKeyNoteType = FourKeyNoteType.NORMAL):
        super().__init__(chart, time, lane, length, type)


class FourKeyChart(Chart[FourKeyNote]):
    ...
