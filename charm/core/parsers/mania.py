from __future__ import annotations

from pathlib import Path

from charm.core.gamemodes.four_key.chart import FourKeyNote, FourKeyChart
from charm.core.generic.metadata import ChartSetMetadata
from charm.core.generic.parser import Parser
from charm.core.generic.chart import ChartMetadata
from charm.core.parsers._osu import OsuHitCircle, OsuHold, RawOsuChart


class ManiaParser(Parser[FourKeyChart]):
    @staticmethod
    def is_possible_chartset(path: Path) -> bool:
        return len(tuple(path.glob('./*.osu'))) > 0

    @staticmethod
    def is_parsable_chart(path: Path) -> bool:
        return path.suffix == ".osu"

    @staticmethod
    def parse_chartset_metadata(path: Path) -> ChartSetMetadata:
        first_chart = next(iter(path.glob('./*.osu')))
        raw_chart = RawOsuChart.parse(first_chart)
        metadata = raw_chart.metadata
        return ChartSetMetadata(path, metadata.title, metadata.artist, charter = metadata.charter, source = metadata.source)

    @staticmethod
    def parse_chart_metadata(path: Path) -> list[ChartMetadata]:
        charts = path.glob('./*.osu')
        metadatas = []
        for chart in charts:
            raw_chart = RawOsuChart.parse(chart)
            metadatas.append(ChartMetadata("4k", raw_chart.metadata.difficulty, chart))
        return metadatas

    @staticmethod
    def parse_chart(chart_data: ChartMetadata) -> list[FourKeyChart]:
        raw_chart = RawOsuChart.parse(chart_data.path)  # SO MUCH is hidden by this function
        chart = FourKeyChart(chart_data, [], [])
        chart.events.extend(raw_chart.timing_points)
        for hit_object in raw_chart.hit_objects:
            if isinstance(hit_object, OsuHitCircle):
                chart.notes.append(FourKeyNote(chart, hit_object.time, hit_object.get_lane(4)))
            elif isinstance(hit_object, OsuHold):
                chart.notes.append(FourKeyNote(chart, hit_object.time, hit_object.get_lane(4), length = hit_object.length))

        chart.events.extend(Parser.calculate_countdowns(chart))
        chart.events.sort()

        return [chart]
