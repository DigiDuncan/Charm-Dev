from __future__ import annotations

from collections.abc import Sequence
from enum import StrEnum

from charm.lib.types import Seconds

from charm.core.generic import Chart, Event, Note, ChartMetadata


class TaikoNoteType(StrEnum):
    KAT = "kat"
    DON = "don"
    DENDEN = "denden"
    DRUMROLL = "drumroll"


class TaikoNote(Note):
    def __init__(self, chart: TaikoChart, time: Seconds, lane: int, length: Seconds = 0, type: TaikoNoteType = TaikoNoteType.KAT, *, large: bool = False):
        super().__init__(chart, time, lane, length, type)
        self.chart: TaikoChart
        self.type: TaikoNoteType
        self.parent: TaikoNote
        self.large = large


class TaikoChart(Chart):
    def __init__(self, metadata: ChartMetadata, notes: Sequence[TaikoNote], events: Sequence[Event]) -> None:
        super().__init__(metadata, notes, events)
        self.notes: list[TaikoNote]
