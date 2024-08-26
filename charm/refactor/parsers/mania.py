from __future__ import annotations

from pathlib import Path

from charm.lib.gamemodes.osu import OsuHold
from charm.refactor.charts.four_key import FourKeyNote, FourKeyChart
from charm.refactor.generic.parser import Parser
from charm.refactor.generic.chart import ChartMetadata
from charm.refactor.parsers._osu import OsuHitCircle, RawOsuChart


class ManiaParser(Parser[FourKeyChart]):
    @staticmethod
    def parse_metadata(path: Path) -> list[ChartMetadata]:
        return []

    @staticmethod
    def parse_chart(chart_data: ChartMetadata) -> list[FourKeyChart]:
        raise NotImplementedError

    @classmethod
    def parse(cls, path: Path) -> list[FourKeyChart]:
        chart_files = path.glob("*.osu")
        charts = []

        # added_bpm_events = False

        for p in chart_files:
            raw_chart = RawOsuChart.parse(p)  # SO MUCH is hidden by this function
            chart = FourKeyChart("4k", raw_chart.metadata.difficulty)
            # !: Removed this! Is it even used? If it is, aaa!
            # if not added_bpm_events:
            #     song.events.extend(raw_chart.timing_points)
            #     added_bpm_events = True
            for hit_object in raw_chart.hit_objects:
                if isinstance(hit_object, OsuHitCircle):
                    chart.notes.append(FourKeyNote(chart, hit_object.time, hit_object.get_lane(4)))
                elif isinstance(hit_object, OsuHold):
                    chart.notes.append(FourKeyNote(chart, hit_object.time, hit_object.get_lane(4), length = hit_object.length))
            charts.append(chart)
        # TODO: Handle no charts
        return charts
