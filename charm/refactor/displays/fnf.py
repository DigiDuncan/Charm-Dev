from __future__ import annotations

from typing import TYPE_CHECKING

from charm.refactor.charts.four_key import FourKeyChart
from charm.refactor.engines.fnf import FNFEngine
from charm.refactor.generic.display import Display
from charm.refactor.generic.chartset import ChartSet

if TYPE_CHECKING:
    from charm.lib.digiwindow import DigiWindow

class FNFDisplay(Display[FNFEngine, FourKeyChart]):

    def __init__(self, engine: FNFEngine, charts: tuple[FourKeyChart, ...]):
        super().__init__(engine, charts)
        assert len(charts) == 2, "FNF expects two charts. [0] for the player, [1] for the opposition"
        self.player_chart: FourKeyChart
        self.opp_chart: FourKeyChart
        self.player_chart, self.opp_chart = charts
