from collections.abc import Sequence
from pathlib import Path

from charm.core.generic import ChartSetMetadata, Parser, ChartMetadata
from charm.core.gamemodes.taiko import TaikoNote, TaikoChart, TaikoNoteType
from ._osu import OsuHitCircle, OsuSlider, OsuSpinner, RawOsuChart


class TaikoParser(Parser):
    gamemode = "taiko"

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
        metadatas: list[ChartMetadata] = []
        for chart in charts:
            raw_chart = RawOsuChart.parse(chart)
            metadatas.append(ChartMetadata("taiko", raw_chart.metadata.difficulty, chart))
        return metadatas

    @staticmethod
    def parse_chart(chart_data: ChartMetadata) -> Sequence[TaikoChart]:
        raw_chart = RawOsuChart.parse(chart_data.path)  # SO MUCH is hidden by this function
        chart = TaikoChart(chart_data, [], [])
        chart.events.extend(raw_chart.timing_points)
        for hit_object in raw_chart.hit_objects:
            if isinstance(hit_object, OsuHitCircle):
                if hit_object.taiko_kat:
                    chart.notes.append(TaikoNote(chart, hit_object.time, 0, 0, TaikoNoteType.KAT, large = hit_object.taiko_large))
                else:
                    chart.notes.append(TaikoNote(chart, hit_object.time, 0, 0, TaikoNoteType.DON, large = hit_object.taiko_large))
            elif isinstance(hit_object, OsuSlider):
                chart.notes.append(TaikoNote(chart, hit_object.time, 0, hit_object.length, TaikoNoteType.DRUMROLL, large = hit_object.taiko_large))
            elif isinstance(hit_object, OsuSpinner):
                chart.notes.append(TaikoNote(chart, hit_object.time, 0, hit_object.length, TaikoNoteType.DENDEN, large = hit_object.taiko_large))

        chart.events.extend(Parser.calculate_countdowns(chart))
        chart.events.sort()

        return [chart]
