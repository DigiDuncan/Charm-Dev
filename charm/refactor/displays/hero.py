from charm.refactor.charts.hero import HeroChart
from charm.refactor.engines.hero import HeroEngine
from charm.refactor.generic.display import Display


class HeroDisplay(Display[HeroEngine, HeroChart]):
    ...
