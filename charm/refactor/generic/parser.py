from pathlib import Path
from charm.refactor.generic.chart import Chart

class Parser[T: Chart]:
    @classmethod
    def parse_metadata(cls, path: Path) -> list[T]:
        """
        Without detailing the note or event data find all of the charts of this gamemode
        found within the given and resolve the minimum needed info.
        """
        raise NotImplementedError

    @classmethod
    def parse_chart(cls, chart: T) -> list[T]:
        """
        For the specific chart provided read its source, and create
        the needed note and event data.

        ! Because of FNF this method may not return only one chart.
        """
        raise NotImplementedError
