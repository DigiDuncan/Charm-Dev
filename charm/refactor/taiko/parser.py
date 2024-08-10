from pathlib import Path
from charm.lib.errors import NoChartsErrorByPath
from charm.refactor.generic.parser import Parser
from charm.refactor.taiko.chart import TaikoNote, TaikoChart, TaikoNoteType
from charm.refactor.taiko.chartset import TaikoChartSet
from charm.refactor.util.parser_osu import OsuHitCircle, OsuSlider, OsuSpinner, RawOsuChart

class TaikoParser(Parser):
    @classmethod
    def parse_chartset(cls, path: Path) -> TaikoChartSet:
        """path: Path to osu chartset folder
        """
        chart_paths = cls.get_chart_paths(path)
        charts = [cls.parse_chart(p) for p in chart_paths]
        if len(charts) == 0:
            raise NoChartsErrorByPath(path)
        chartset = TaikoChartSet(path, charts)
        return chartset

    @classmethod
    def get_chart_paths(cls, path: Path) -> list[Path]:
        return list(path.glob("*.osu"))

    @classmethod
    def parse_chart(cls, path: Path) -> TaikoChart:
        raw_chart = RawOsuChart.parse(path)  # SO MUCH is hidden by this function
        chart = TaikoChart("taiko", raw_chart.metadata.difficulty)
        # !: Removed this! Is it even used? If it is, aaa!
        # if not added_bpm_events:
        #     song.events.extend(raw_chart.timing_points)
        #     added_bpm_events = True
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
        return chart
