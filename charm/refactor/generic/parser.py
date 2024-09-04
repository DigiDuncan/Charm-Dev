import itertools
from pathlib import Path
from charm.refactor.generic.chart import Chart, CountdownEvent, Note
from charm.refactor.generic.metadata import ChartMetadata, ChartSetMetadata

# should be configurable
COUNTDOWN_GAP = 5.0

class Parser[T: Chart[Note]]:
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

    @staticmethod
    def calculate_countdowns(chart: T) -> list[CountdownEvent]:
        countdowns = []
        notes = [Note(chart, -3, 0, 0), *chart.notes]
        for note1, note2 in itertools.pairwise(notes):
            if note2.time - note1.time >= COUNTDOWN_GAP:
                countdowns.append(CountdownEvent(note1.time, note2.time - note1.time))
        return countdowns
