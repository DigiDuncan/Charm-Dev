from pathlib import Path
from charm.refactor.generic.chart import Chart, ChartMetadata

class Parser[T: Chart]:
    @staticmethod
    def parse_metadata(path: Path) -> list[ChartMetadata]:
        """
        Without detailing the note or event data find all of the charts of this gamemode
        found within the given and resolve the minimum needed info.
        """
        raise NotImplementedError

    @staticmethod
    def parse_chart(chart_data: ChartMetadata) -> list[T]:
        """
        For the specific chart provided read its source, and create
        the needed note and event data.

        ! Because of FNF this method may not return only one chart.
        """
        raise NotImplementedError
