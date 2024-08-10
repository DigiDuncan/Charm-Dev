from charm.refactor.fourkey.chart import FourKeyChart
from charm.refactor.fnf.engine import FNFEngine
from charm.refactor.fourkey.engine import FourKeyEngine
from charm.refactor.generic.display import Display


class FourKeyDisplay(Display[FNFEngine | FourKeyEngine, FourKeyChart]):
    ...
