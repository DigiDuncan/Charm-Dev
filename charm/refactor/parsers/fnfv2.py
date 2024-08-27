# Welcome to my personal hell.
# "Oh, we'll just have all the FNF parsers in one object,"
# "I'm sure the difference between the engines isn't that bad!"
# Which is true! Except for when FNF team in their infinite wisdom
# decides it's high time for a version 2, well after an entire community
# got used to the first one and created a ton of content surrounding it,
# that is not only completely incompatible but works entirely differently.

# Ways this breaks our understanding of FNF:
# - A seperate metadata file is supplied
# - All diffculties are in one chart file*
# - *except remixes because those are in a different file and use different audio
# so they shouldn't even share a folder but they do
# - Information from the metadata file is required to parse the chart
# - Importantly for Charm, these new files are indistinguishable from the old style
# without first opening them

# Listen, man, I didn't want Charm to 50% FNF either; I keep having to focus on it
# because it throws the most curveballs.
# Well-defined chart formats for the win. I need to make my own at this point.

# Here we go.

import json
from pathlib import Path
from typing import Any, Literal, TypedDict
from charm.refactor.charts.fnf import FNFChart, FNFNote, FNFNoteType
from charm.refactor.generic.chart import ChartMetadata
from charm.refactor.generic.parser import Parser

TimeFormat = Literal["s", "ms"]

class EventJSON(TypedDict):
    t: float
    e: str
    v: dict[str, Any]

class NoteJSON(TypedDict):
    t: float
    d: int
    l: float

class NoteWithDataJSON(TypedDict):
    t: float
    d: int
    l: float
    k: str

class SongFileJSON(TypedDict):
    version: str
    scrollSpeed: dict[str, float]
    events: list[EventJSON]
    notes: dict[str, list[NoteJSON | NoteWithDataJSON]]

class PlayDataJSON(TypedDict):
    album: str
    previewStart: int
    previewEnd: int
    stage: str
    characters: dict[str, str]
    ratings: dict[str, int]
    difficulties: list[str]
    noteStyle: str

class TimeChangesJSON(TypedDict):
    d: int
    n: int
    t: float
    bt: list[int]
    bpm: float

class MetadataJSON(TypedDict):
    timeFormat: TimeFormat
    artist: str
    charter: str
    playData: PlayDataJSON
    songName: str
    timeChanges: list[TimeChangesJSON]
    generatedBy: str
    version: str

class FNFV2Parser(Parser[FNFChart]):
    @staticmethod
    def is_parseable(path: Path) -> bool:
        if path.suffix != ".json":
            return 0
        else:
            with open(p, encoding = "utf-8") as f:
                try:
                    j = json.load(f)
                except json.JSONDecodeError:
                    return False
                if "version" not in j:
                    return False
                else:
                    try:
                        v = int(j["version"].split(".")[0])
                        return v >= 2
                    except ValueError:
                        return False

    @staticmethod
    def parse_metadata(path: Path) -> list[ChartMetadata]:
        stem = path.stem
        chart_path = path / (stem + "-chart.json")
        meta_path = path / (stem + "-metadata.json")
        with open(meta_path) as m:
            metadata: MetadataJSON = json.load(m)
        metadatas = []
        for d in metadata["playData"]["difficulties"]:
            metadatas.append(ChartMetadata("fnf", d, chart_path, '0'))
        return metadatas

    @staticmethod
    def parse_chart(chart_data: ChartMetadata) -> list[FNFChart]:
        with open(chart_data.path) as p:
            j: SongFileJSON = json.load(p)

        fnf_metadata_path = chart_data.path.parent / (chart_data.path.parent.stem + "-metadata.json")
        with open(fnf_metadata_path) as m:
            metadata: MetadataJSON = json.load(m)

        p1_metadata = ChartMetadata(chart_data.gamemode, chart_data.difficulty, chart_data.path, "1")
        p2_metadata = ChartMetadata(chart_data.gamemode, chart_data.difficulty, chart_data.path, "2")
        charts = [
            FNFChart(p1_metadata, [], [], metadata["timeChanges"][0]["bpm"]),
            FNFChart(p2_metadata, [], [], metadata["timeChanges"][0]["bpm"])
        ]

        # Lanemap: (player, lane, type)
        fnf_overrides = None
        override_path = chart_data.path.parent / "fnf.json"
        if override_path.exists() and override_path.is_file():
            with open(override_path) as f:
                fnf_overrides = json.load(f)
        if fnf_overrides:
            # This is done because some mods use "extra lanes" differently, so I have to provide
            # a file that maps them to the right lane.
            lanemap = [(lane[0], lane[1], getattr(FNFNoteType, lane[2])) for lane in fnf_overrides["lanes"]]
        else:
            lanemap: list[tuple[int, int, FNFNoteType]] = [(0, 0, FNFNoteType.NORMAL), (0, 1, FNFNoteType.NORMAL), (0, 2, FNFNoteType.NORMAL), (0, 3, FNFNoteType.NORMAL),
                                                           (1, 0, FNFNoteType.NORMAL), (1, 1, FNFNoteType.NORMAL), (1, 2, FNFNoteType.NORMAL), (1, 3, FNFNoteType.NORMAL)]

        difficulty = j["notes"][chart_data.difficulty]
        for note in difficulty:
            player, lane, note_type = lanemap[note["d"]]
            time = note["t"] if metadata["timeFormat"] == "s" else note["t"] / 1000
            n = (FNFNote(charts[player], time, lane, note["l"] if metadata["timeFormat"] == "s" else note["l"] / 1000, note_type))
            if "k" in note:
                n.extra_data = (note["k"], )
            charts[player].notes.append(n)

            # TODO: SUSTAINS
            # They don't work right now because I kinda just want to get rid of the hacked sustains ASAP
            # And rewriting how the old ones work in this new parser adds so much complexity that I'd rather
            # not deal with right now.

        return charts
