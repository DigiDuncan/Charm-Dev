from pathlib import Path
from charm.refactor.generic.chart import Chart
from charm.refactor.generic.metadata import ChartMetadata, ChartSetMetadata

class Parser[T: Chart]:
    @staticmethod
    def is_possible_chartset(path: Path) -> bool:
        """Does this folder contain a parseable ChartSet?"""
        return False

    @staticmethod
    def is_parsable_chart(path: Path) -> bool:
        """Is this chart parsable by this Parser"""
        return False

    @staticmethod
    def parse_chartset_metadata(path: Path) -> ChartSetMetadata:
        raise NotImplementedError

    @staticmethod
    def parse_chart_metadata(path: Path) -> list[ChartMetadata]:
        """
        Without detailing the note or event data find all of the charts of this gamemode
        found within the given and resolve the minimum needed info.
        """
        return []

    @staticmethod
    def parse_chart(chart_data: ChartMetadata) -> list[T]:
        """
        For the specific chart provided read its source, and create
        the needed note and event data.

        ! Because of FNF this method may not return only one chart.
        """
        raise NotImplementedError
