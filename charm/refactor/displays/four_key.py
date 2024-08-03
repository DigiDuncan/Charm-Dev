from charm.refactor.charts.four_key import FourKeyChart
from charm.refactor.engines.fnf import FNFEngine
from charm.refactor.engines.four_key import FourKeyEngine
from charm.refactor.generic.display import Display


class FourKeyDisplay(Display[FNFEngine | FourKeyEngine, FourKeyChart]):
    ...
