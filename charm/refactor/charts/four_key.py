from __future__ import annotations

from enum import StrEnum
import logging
from charm.refactor.generic.chart import Chart, Note

logger = logging.getLogger("charm")

class FourKeyNoteType(StrEnum):
    NORMAL = "normal"
    BOMB = "bomb"
    DEATH = "death"
    HEAL = "heal"
    CAUTION = "caution"
    STRIKELINE = "strikeline"
    SUSTAIN = "sustain"  # FNF specific and maybe going away one day

FourKeyNote = Note[FourKeyNoteType]

class FourKeyChart(Chart[FourKeyNote]):
    def __init__(self, difficulty: str, instrument: str = "4k", hash: str | None = None):
        super().__init__(difficulty, instrument, 4, hash)
