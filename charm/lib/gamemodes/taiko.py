from dataclasses import dataclass
from pathlib import Path
from charm.lib.gamemodes.osu import OsuHitCircle, OsuSlider, OsuSpinner, RawOsuChart
from charm.lib.generic.engine import Engine
from charm.lib.generic.highway import Highway
from charm.lib.generic.song import Chart, Metadata, Note, Song


class NoteType:
    DON = "don"
    KAT = "kat"
    DRUMROLL = "drumroll"
    DENDEN = "denden"

@dataclass
class TaikoNote(Note):
    large: bool = False

class TaikoChart(Chart):
    def __init__(self, song: 'Song', difficulty: str, hash: str) -> None:
        super().__init__(song, "taiko", difficulty, "taiko", 4, hash)
        self.song: TaikoSong = song

class TaikoSong(Song):
    def __init__(self, path: Path):
        super().__init__(path)

    @classmethod
    def parse(self, folder: Path) -> "TaikoSong":
        song = TaikoSong(folder)

        chart_files = folder.glob("*.osu")

        added_bpm_events = False

        for p in chart_files:
            raw_chart = RawOsuChart.parse(p)
            chart = TaikoChart(song, raw_chart.metadata.difficulty, None)
            if not added_bpm_events:
                song.events.extend(raw_chart.timing_points)
                added_bpm_events = True
            for hit_object in raw_chart.hit_objects:
                if isinstance(hit_object, OsuHitCircle):
                    if hit_object.taiko_kat:
                        chart.notes.append(TaikoNote(chart, hit_object.time, 0, 0, NoteType.KAT, large = hit_object.taiko_large))
                    else:
                        chart.notes.append(TaikoNote(chart, hit_object.time, 0, 0, NoteType.DON, large = hit_object.taiko_large))
                elif isinstance(hit_object, OsuSlider):
                    chart.notes.append(TaikoNote(chart, hit_object.time, 0, hit_object.length, NoteType.DRUMROLL, large = hit_object.taiko_large))
                elif isinstance(hit_object, OsuSpinner):
                    chart.notes.append(TaikoNote(chart, hit_object.time, 0, hit_object.length, NoteType.DENDEN, large = hit_object.taiko_large))
            song.charts.append(chart)

    @classmethod
    def get_metadata(self, folder: Path) -> Metadata:
        chart_files = folder.glob("*.osu")
        raw_chart = RawOsuChart.parse(next(chart_files))
        m = raw_chart.metadata
        return Metadata(
            m.title,
            m.artist,
            m.source,
            charter = m.charter,
            path = folder,
            gamemode = "taiko"
        )

class TaikoEngine(Engine):
    pass

class TaikoHighway(Highway):
    pass
