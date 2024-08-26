from pathlib import Path
from charm.refactor.charts.hero import HeroChart
from charm.refactor.generic.chart import ChartMetadata
from charm.refactor.generic.parser import Parser


class HeroParser(Parser[HeroChart]):
    @staticmethod
    def parse_metadata(path: Path) -> list[ChartMetadata]:
        return []

    @staticmethod
    def parse_chart(chart_data: ChartMetadata) -> list[HeroChart]:
        raise NotImplementedError
