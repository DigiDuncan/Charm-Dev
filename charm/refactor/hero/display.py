from charm.refactor.hero.chart import HeroChart
from charm.refactor.hero.engine import HeroEngine
from charm.refactor.generic.display import Display


class HeroDisplay(Display[HeroEngine, HeroChart]):
    ...
