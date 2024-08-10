from hashlib import sha1
from io import StringIO
import itertools
from pathlib import Path

import simfile
from simfile.types import Simfile
from simfile.sm import SMChart
from simfile.ssc import SSCChart
from simfile.notes import NoteData
from simfile.notes.group import group_notes, NoteWithTail
from simfile.timing import TimingData, BeatValue
from simfile.timing.engine import TimingEngine

from charm.lib.errors import NoChartsErrorByPath
from charm.refactor.fourkey.chart import FourKeyNoteType, FourKeyNote, FourKeyChart
from charm.refactor.fourkey.chartset import FourKeyChartSet
from charm.refactor.generic.chart import BPMChangeEvent
from charm.refactor.generic.parser import Parser

sm_name_map = {
    "TAP": FourKeyNoteType.NORMAL,
    "MINE": FourKeyNoteType.BOMB
}


class SMParser(Parser):
    @classmethod
    def parse_chartset(cls, path: Path) -> FourKeyChartSet:
        """path: Path to fourkey chartset folder
        """
        sm_path = cls.get_smfile_path(path)

        # OK, figure out what chart file to use.
        with sm_path.open("r") as f:
            sm = simfile.load(f)

        charts: list[FourKeyChart] = []

        # !: THIS PARSER RELIES ON THE smfile LIBRARY (PROBABLY TOO MUCH)
        # This means I *don't know how this works*
        # The only reason SM long notes are scored right now is because smfile gives us a handy TimingEngine
        # and this is great but breaks parity with every other system we have!
        # Need to figure how to a) not use TimingEngine for SMEngine, and b) maybe not use this library at all
        # for parsing? But it's so good...

        charts = [cls.parse_chart(sm, raw_chart) for raw_chart in sm.charts]
        chartset = FourKeyChartSet(path, charts)
        return chartset

    @classmethod
    def get_smfile_path(cls, path: Path) -> Path:
        try:
            return next(itertools.chain(path.glob("*.ssc"), path.glob("*.sm")))
        except StopIteration:
            raise NoChartsErrorByPath(path) from None

    @classmethod
    def get_chart_paths(cls, path: Path) -> list[Path]:
        return list(path.glob(f"{path.name}*.json"))

    @classmethod
    def parse_chart(cls, sm: Simfile, raw_chart: SMChart | SSCChart) -> FourKeyChart:
        chart = FourKeyChart("4k", raw_chart.difficulty)
        temp_file = StringIO()
        raw_chart.serialize(temp_file)
        chart.hash = sha1(bytes(temp_file.read(), encoding = "utf-8")).hexdigest()

        # Use simfile to make our life so much easier.
        notedata = NoteData(raw_chart)
        grouped_notes = group_notes(notedata, join_heads_to_tails=True)
        timing = TimingData(sm, raw_chart)
        timing_engine = TimingEngine(timing)
        self.timing_engine = timing_engine

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

        return chart
