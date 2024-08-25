from pathlib import Path
from charm.refactor.charts.hero import HeroChart
from charm.refactor.generic.parser import Parser


class HeroParser(Parser[HeroChart]):
    @classmethod
    def parse_metadata(cls, path: Path) -> list[HeroChart]:
        return []

    @classmethod
    def parse_chart(cls, chart: HeroChart) -> list[HeroChart]:
        return super().parse_chart(chart)
