from collections.abc import Sequence
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

from charm.game.generic.metadata import ChartSetMetadata
from charm.lib.errors import NoChartsError

from charm.game.generic import BPMChangeEvent, ChartMetadata, Parser
from charm.game.gamemodes.four_key import FourKeyNoteType, FourKeyNote, FourKeyChart

SM_NAME_MAP = {
    "TAP": FourKeyNoteType.NORMAL,
    "MINE": FourKeyNoteType.BOMB
}


class SMParser(Parser):
    gamemode = "4k"

    @staticmethod
    def is_possible_chartset(path: Path) -> bool:
        return len([f for f in path.iterdir() if f.suffix in {'.ssc', '.sm'}]) > 0

    @staticmethod
    def is_parsable_chart(path: Path) -> bool:
        return path.suffix in {'.sm', '.ssc'}

    @staticmethod
    def parse_chart_metadata(path: Path) -> list[ChartMetadata]:
        # Both SMFile and SSCFile have the song metadata in them. Having to parse the whole object kinda sucks
        # but untill we write our own we are s*** out of luck.

        metadatas = []
        charts = SMParser._parse(path)
        chart_path = [f for f in path.iterdir() if f.suffix in {'.sm', '.ssc'}][0]
        for d in charts.keys():
            metadatas.append(ChartMetadata("4k", d, chart_path))
        return metadatas

    @staticmethod
    def parse_chartset_metadata(path: Path) -> ChartSetMetadata:
        # Both SMFile and SSCFile have the song metadata in them. Having to parse the whole object kinda sucks
        # but untill we write our own we are s*** out of luck.
        try:
            sm_file = next(itertools.chain(path.glob("*.ssc"), path.glob("*.sm")))
        except StopIteration as err:
            raise NoChartsError(path.stem) from err
        with sm_file.open("r") as f:
            sm = simfile.load(f)

        return ChartSetMetadata(path,
                                sm.title,
                                sm.artist,
                                sm.cdtitle,
                                genre = sm.genre,
                                album_art = getattr(sm, "cdimage", None),
                                gamemode = "4k")

    @staticmethod
    def parse_chart(chart_data: ChartMetadata) -> Sequence[FourKeyChart]:
        # The simfile parsers return a list of charts which all have their difficulty so it
        # shouldn't be hard to find and parse only the one we care about.
        charts = SMParser._parse(chart_data.path.parent)
        if chart_data.difficulty not in charts.keys():
            raise NoChartsError(str(chart_data.path))
        c = charts[chart_data.difficulty]
        c.metadata = chart_data
        return [c]

    @staticmethod
    def _parse(path: Path) -> dict[str, FourKeyChart]:
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
            c: SMChart | SSCChart
            chart = FourKeyChart(..., [], [])
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
                note_type = SM_NAME_MAP.get(note.note_type.name, None)
                if isinstance(note, NoteWithTail):
                    end_time = timing_engine.time_at(note.tail_beat)
                    chart.notes.append(FourKeyNote(chart, time, note.column, end_time - time, FourKeyNoteType.NORMAL))
                else:
                    chart.notes.append(FourKeyNote(chart, time, note.column, 0, note_type))

            for bpm in timing.bpms.data:
                bpm: BeatValue = bpm
                bpm_event = BPMChangeEvent(timing_engine.time_at(bpm.beat), float(bpm.value))
                chart.events.append(bpm_event)

        return charts
