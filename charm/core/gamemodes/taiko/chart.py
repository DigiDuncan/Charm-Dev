from __future__ import annotations

from enum import StrEnum

from charm.lib.types import Seconds

from charm.core.generic import Chart, Note


class TaikoNoteType(StrEnum):
    KAT = "kat"
    DON = "don"
    DENDEN = "denden"
    DRUMROLL = "drumroll"


class TaikoNote(Note["TaikoChart", TaikoNoteType]):
    def __init__(self, chart: TaikoChart, time: Seconds, lane: int, length: Seconds = 0, type: TaikoNoteType = TaikoNoteType.KAT, *, large: bool = False):
        super().__init__(chart, time, lane, length, type)
        self.large = large


class TaikoChart(Chart[TaikoNote]):
    ...
