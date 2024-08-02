from pathlib import Path
from charm.refactor.generic.parser import Parser
from charm.refactor.charts.taiko import TaikoNote, TaikoChart, TaikoNoteType
from charm.refactor.parsers._osu import OsuHitCircle, OsuSlider, OsuSpinner, RawOsuChart

class TaikoParser(Parser[TaikoChart]):
    def __init__(self, path: Path):
        super().__init__(path)

    def parse(self) -> list[TaikoChart]:
        chart_files = self.path.glob("*.osu")
        charts = []

        # added_bpm_events = False

        for p in chart_files:
            raw_chart = RawOsuChart.parse(p)  # SO MUCH is hidden by this function
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
            charts.append(chart)
        # TODO: Handle no charts
        return charts
