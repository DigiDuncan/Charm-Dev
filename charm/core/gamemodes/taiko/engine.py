
from charm.lib.types import Seconds

from charm.core.generic import Engine
from .chart import TaikoChart, TaikoNote

class TaikoEngine(Engine[TaikoChart, TaikoNote]):
    def __init__(self, chart: TaikoChart, offset: Seconds = 0):
        super().__init__(chart, None, offset)
