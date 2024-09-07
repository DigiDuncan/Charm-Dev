from __future__ import annotations

from collections.abc import Sequence
from enum import StrEnum

from charm.lib.types import Seconds

from charm.core.generic import Chart, Event, Note, ChartMetadata


class FourKeyNoteType(StrEnum):
    NORMAL = "normal"
    BOMB = "bomb"
    DEATH = "death"
    HEAL = "heal"
    CAUTION = "caution"
    STRIKELINE = "strikeline"
    SUSTAIN = "sustain"  # FNF specific and maybe going away one day


class FourKeyNote(Note):
    def __init__(self, chart: FourKeyChart, time: Seconds, lane: int, length: Seconds = 0, type: FourKeyNoteType = FourKeyNoteType.NORMAL):
        super().__init__(chart, time, lane, length, type)
        self.chart: FourKeyChart
        self.type: FourKeyNoteType
        self.parent: FourKeyNote


class FourKeyChart(Chart):
    def __init__(self, metadata: ChartMetadata, notes: Sequence[FourKeyNote], events: Sequence[Event]) -> None:
        super().__init__(metadata, notes, events)
        self.notes: list[FourKeyNote]
