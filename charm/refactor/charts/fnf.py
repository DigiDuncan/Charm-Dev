# !: This stub will be gone eventually!
# It's here because there's currently no gamemode definitions
# so it's unclear why FNFParser -> FourKeyChart.

from dataclasses import dataclass
from enum import StrEnum
from charm.refactor.generic.chart import Event, Note, Chart

@dataclass
class CameraFocusEvent(Event):
    focused_player: int

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}@{self.time:.3f} p:{self.focused_player}>"

    def __str__(self) -> str:
        return self.__repr__()

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
