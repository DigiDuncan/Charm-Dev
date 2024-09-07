
from charm.lib.types import Seconds

from charm.core.generic import Engine
from .chart import TaikoChart

class TaikoEngine(Engine):
    def __init__(self, chart: TaikoChart, offset: Seconds = 0):
        super().__init__(chart, None, offset)
        self.chart: TaikoChart
