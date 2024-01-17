from hashlib import sha1
from io import StringIO
import itertools
from pathlib import Path

import simfile
from simfile.sm import SMChart
from simfile.ssc import SSCChart
from simfile.notes import NoteData
from simfile.notes.group import group_notes, NoteWithTail
from simfile.timing import TimingData, BeatValue
from simfile.timing.engine import TimingEngine

from charm.lib.gamemodes.four_key import FourKeyChart, FourKeyEngine, FourKeyNote, FourKeySong, NoteType
from charm.lib.generic.song import BPMChangeEvent, Metadata

sm_to_fnf_name_map = {
    "TAP": NoteType.NORMAL,
    "MINE": NoteType.BOMB
}


class SMSong(FourKeySong):
    def __init__(self, path: Path):
        super().__init__(path)

        self.timing_engine: TimingEngine = None

    @classmethod
    def parse(cls, folder: Path) -> "FourKeySong":
        # OK, figure out what chart file to use.
        files = itertools.chain(folder.glob("*.ssc"), folder.glob("*.sm"))
        sm_file = next(files)
        with open(sm_file, "r") as f:
            sm = simfile.load(f)

        song = FourKeySong(folder)

        charts: dict[str, FourKeyChart] = {}

        for c in sm.charts:
            c: SMChart | SSCChart = c
            chart = FourKeyChart(song, c.difficulty, None)
            temp_file = StringIO()
            c.serialize(temp_file)
            chart.hash = sha1(bytes(temp_file.read())).hexdigest()
            charts[c.difficulty] = chart

            # Use simfile to make our life so much easier.
            notedata = NoteData(c)
            grouped_notes = group_notes(notedata, join_heads_to_tails=True)
            timing = TimingData(sm, c)
            timing_engine = TimingEngine(timing)
            song.timing_engine = timing_engine

            for notes in grouped_notes:
                note = notes[0]
                time = timing_engine.time_at(note.beat)
                beat = note.beat % 1
                value = beat.denominator
                note_type = sm_to_fnf_name_map.get(note.note_type.name, None)
                if isinstance(note, NoteWithTail):
                    end_time = timing_engine.time_at(note.tail_beat)
                    chart.notes.append(FourKeyNote(chart, time, note.column, end_time - time, NoteType.NORMAL, value = value))
                else:
                    chart.notes.append(FourKeyNote(chart, time, note.column, 0, note_type, value = value))

            for bpm in timing.bpms.data:
                bpm: BeatValue = bpm
                bpm_event = BPMChangeEvent(timing_engine.time_at(bpm.beat), float(bpm.value))
                chart.events.append(bpm_event)

        song.charts.extend([v for v in charts.values()])

        return song

    @classmethod
    def get_metadata(self, folder: Path) -> Metadata:
        # OK, figure out what chart file to use.
        files = itertools.chain(folder.glob("*.ssc"), folder.glob("*.sm"))
        sm_file = next(files)
        with open(sm_file, "r") as f:
            sm = simfile.load(f)
        title = sm.title
        artist = sm.artist
        album = sm.cdtitle
        length = sm.get("musiclength", 0)
        genre = sm.genre
        charter = sm.credit
        return Metadata(title, artist, album,
            length = length, genre = genre, charter = charter, path = folder,
            gamemode = "4k")

class SMEngine(FourKeyEngine):
    def score_sustains(self):
        timing_engine: TimingEngine = self.chart.song.timing_engine
        current_beat = timing_engine.beat_at(self.chart_time)
        time_since_last_tick = self.chart_time - self.last_sustain_tick
        beats_since_last_tick = time_since_last_tick * float(timing_engine.bpm_at(current_beat) / 60)

        sixteenths = int(beats_since_last_tick * 16)
        if sixteenths < 1:
            return

        for sustain in self.active_sustains:
            if self.key_state[sustain.lane]:
                self.hp += int(self.judgements[0].hp_change / 4) * sixteenths  # TODO: Does this feel right?
                self.score += int(self.judgements[0].score / 4) * sixteenths
            else:
                self.hp -= int(self.judgements[0].hp_change / 4) * sixteenths

        self.last_sustain_tick = self.chart_time
