# !: This stub will be gone eventually!
# It's here because there's currently no gamemode definitions
# so it's unclear why FNFParser -> FourKeyChart.

from enum import StrEnum
from charm.refactor.generic.chart import Note, Chart

class FNFNoteType(StrEnum):
    NORMAL = "normal"
    BOMB = "bomb"
    DEATH = "death"
    HEAL = "heal"
    CAUTION = "caution"
    STRIKELINE = "strikeline"
    SUSTAIN = "sustain"  # FNF specific and maybe going away one day

class FNFNote(Note[FNFNoteType]):
    pass

class FNFChart(Chart[FNFNote]):
    pass
