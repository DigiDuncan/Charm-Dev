from dataclasses import dataclass
from enum import StrEnum
from charm.refactor.generic.chart import ChartMetadata, Event, Note, Chart

@dataclass
class CameraFocusEvent(Event):
    focused_player: int
    x_offset: float = 0.0
    y_offset: float = 0.0

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}@{self.time:.3f} p:{self.focused_player} x:{self.x_offset} y:{self.y_offset}>"

    def __str__(self) -> str:
        return self.__repr__()

@dataclass
class CameraZoomEvent(Event):
    zoom: float
    ease: str | None = None
    duration: float = 0.0

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}@{self.time:.3f} z:{self.zoom} e:{self.ease} d:{self.duration}>"

    def __str__(self) -> str:
        return self.__repr__()

@dataclass
class PlayAnimationEvent(Event):
    target: str
    anim: str
    force: bool = False

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}@{self.time:.3f} {self.target}/{self.anim} force:{self.force}>"

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
    def __init__(self, metadata: ChartMetadata, notes: list[FNFNote], events: list[Event], bpm: float) -> None:
        super().__init__(metadata, notes, events, bpm)
        self.speed = 1.0
