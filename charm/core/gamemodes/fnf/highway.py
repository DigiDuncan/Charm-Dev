# !: This stub will be gone eventually!
# It's here because there's currently no gamemode definitions
# so it's unclear why FNFParser -> FourKeyHighway.

from charm.core.gamemodes.fnf.chart import FNFChart
from charm.core.gamemodes.four_key.highway import FourKeyHighway
from charm.core.generic.engine import Engine


class FNFHighway(FourKeyHighway):
    def __init__(self, chart: FNFChart, engine: Engine, pos: tuple[int, int], size: tuple[int, int] | None = None, gap: int = 5):
        super().__init__(chart, engine, pos, size, gap)  # type: ignore reportArgumentType
