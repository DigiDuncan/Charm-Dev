from __future__ import annotations
from typing import NamedTuple, Sequence
from enum import StrEnum

from nindex import Index

from charm.core.generic.metadata import ChartMetadata
from charm.lib.types import Seconds

from charm.core.generic import Chart, Note, Event

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

class FourKeyNIndexCollection(NamedTuple):
    notes: Index[Seconds, FourKeyNote]
    events: Index[Seconds, Event]

class FourKeyChart(Chart[FourKeyNote]):
    def __init__(self, metadata: ChartMetadata, notes: Sequence[FourKeyNote], events: Sequence[Event]) -> None:
        super().__init__(metadata, notes, events)
        self.indices: FourKeyNIndexCollection


    def calculate_indices(self) -> None:
        self.indices = FourKeyNIndexCollection(
            Index[Seconds, FourKeyNote](self.notes, 'time'),
            Index[Seconds, Event](self.events, 'time')
        )
