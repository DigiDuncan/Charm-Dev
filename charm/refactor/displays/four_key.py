from charm.refactor.charts.four_key import FourKeyChart
from charm.refactor.engines.fnf import FNFEngine
from charm.refactor.engines.sm import SMEngine
from charm.refactor.generic.display import Display


class FourKeyDisplay(Display[FNFEngine | SMEngine, FourKeyChart]):
    ...
