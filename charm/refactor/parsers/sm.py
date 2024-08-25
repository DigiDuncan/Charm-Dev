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

from charm.lib.errors import NoChartsError
from charm.refactor.charts.four_key import FourKeyNoteType, FourKeyNote, FourKeyChart
from charm.refactor.generic.chart import BPMChangeEvent
from charm.refactor.generic.parser import Parser

sm_name_map = {
    "TAP": FourKeyNoteType.NORMAL,
    "MINE": FourKeyNoteType.BOMB
}

class SMParser(Parser[FourKeyChart]):
    @classmethod
    def parse_metadata(cls, path: Path) -> list[FourKeyChart]:
        return []

    @classmethod
    def parse_chart(cls, chart: FourKeyChart) -> list[FourKeyChart]:
        return super().parse_chart(chart)

    def parse(self, path: Path) -> list[FourKeyChart]:
        # OK, figure out what chart file to use.
        try:
            sm_file = next(itertools.chain(path.glob("*.ssc"), path.glob("*.sm")))
        except StopIteration as err:
            raise NoChartsError(path.stem) from err
        with sm_file.open("r") as f:
            sm = simfile.load(f)

        charts: dict[str, FourKeyChart] = {}

        # !: THIS PARSER RELIES ON THE smfile LIBRARY (PROBABLY TOO MUCH)
        # This means I *don't know how this works*
        # The only reason SM long notes are scored right now is because smfile gives us a handy TimingEngine
        # and this is great but breaks parity with every other system we have!
        # Need to figure how to a) not use TimingEngine for SMEngine, and b) maybe not use this library at all
        # for parsing? But it's so good...

        for c in sm.charts:
            c: SMChart | SSCChart = c
            chart = FourKeyChart("4k", c.difficulty)
            temp_file = StringIO()
            c.serialize(temp_file)
            chart.hash = sha1(bytes(temp_file.read(), encoding = "utf-8")).hexdigest()
            charts[c.difficulty] = chart

            # Use simfile to make our life so much easier.
            notedata = NoteData(c)
            grouped_notes = group_notes(notedata, join_heads_to_tails=True)
            timing = TimingData(sm, c)
            timing_engine = TimingEngine(timing)
            timing_engine = timing_engine

            for notes in grouped_notes:
                note = notes[0]
                time = timing_engine.time_at(note.beat)
                beat = note.beat % 1
                value = beat.denominator  # TODO: Reimplement?
                note_type = sm_name_map.get(note.note_type.name, None)
                if isinstance(note, NoteWithTail):
                    end_time = timing_engine.time_at(note.tail_beat)
                    chart.notes.append(FourKeyNote(chart, time, note.column, end_time - time, FourKeyNoteType.NORMAL))
                else:
                    chart.notes.append(FourKeyNote(chart, time, note.column, 0, note_type))

            for bpm in timing.bpms.data:
                bpm: BeatValue = bpm
                bpm_event = BPMChangeEvent(timing_engine.time_at(bpm.beat), float(bpm.value))
                chart.events.append(bpm_event)

        return list(charts.values())
