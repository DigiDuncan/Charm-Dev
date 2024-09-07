from charm.lib.types import Seconds

from charm.core.generic import Engine
from .chart import HeroChart, HeroNote


class HeroEngine(Engine):
    def __init__(self, chart: HeroChart, offset: Seconds = 0):
        super().__init__(chart, None, offset)
        self.chart: HeroChart
        self.current_notes: list[HeroNote]
