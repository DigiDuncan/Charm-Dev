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

class FourKeyNote(Note[FourKeyNoteType]):
    pass

class FourKeyChart(Chart[FourKeyNote]):
    pass
