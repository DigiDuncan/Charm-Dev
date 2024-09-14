import itertools
from pathlib import Path
from collections.abc import Sequence

from .chart import BaseChart, CountdownEvent
from .metadata import ChartMetadata, ChartSetMetadata

# should be configurable
COUNTDOWN_GAP = 5.0

class Parser:
    gamemode: str = None

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
    def parse_chart(chart_data: ChartMetadata) -> Sequence[BaseChart]:
        """
        For the specific chart provided read its source, and create
        the needed note and event data.

        ! Because of FNF this method may not return only one chart.
        """
        raise NotImplementedError

    @staticmethod
    def calculate_countdowns(chart: BaseChart) -> list[CountdownEvent]:
        countdowns = [
            CountdownEvent(-3, chart.notes[0].time + 3),
            *(
                CountdownEvent(note1.time, note2.time - note1.time)
                for note1, note2 in itertools.pairwise(chart.notes)
                if note2.time - note1.time >= COUNTDOWN_GAP
            )
        ]
        return countdowns
