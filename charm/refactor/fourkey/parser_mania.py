from __future__ import annotations

from pathlib import Path

from charm.lib.errors import NoChartsErrorByPath
from charm.lib.gamemodes.osu import OsuHold
from charm.refactor.fourkey.chart import FourKeyNote, FourKeyChart
from charm.refactor.fourkey.chartset import FourKeyChartSet
from charm.refactor.generic.parser import Parser
from charm.refactor.util.parser_osu import OsuHitCircle, RawOsuChart


class ManiaParser(Parser):
    @classmethod
    def parse_chartset(cls, path: Path) -> FourKeyChartSet:
        chart_paths = cls.get_chart_paths(path)
        charts = [cls.parse_chart(p) for p in chart_paths]
        if len(charts) == 0:
            raise NoChartsErrorByPath(path)
        chartset = FourKeyChartSet(path, charts)
        return chartset

    @classmethod
    def get_chart_paths(cls, path: Path) -> list[Path]:
        return list(path.glob("*.osu"))

    @classmethod
    def parse_chart(cls, path: Path) -> FourKeyChart:
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
        return chart
