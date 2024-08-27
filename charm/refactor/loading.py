#
# -- CHARTSET AND CHART LOADING --
#
#   Before the unified menu can show the full list
#   charm needs to find all of the songs and charts.
#   To save time only the song metadata, and bare minimum
#   for each chart is found.
#
#   ! This is currently done per gamemode folder, but if a mod
#   ! in the future wants to mix gamemodes this will need updating.
import json
from typing import NamedTuple
from collections.abc import Callable
from pathlib import Path
import os

from charm.lib.paths import songspath

from charm.refactor.generic.chartset import ChartSet
from charm.refactor.generic.chart import Chart, ChartMetadata

# -- PARSERS --
from charm.refactor.generic.parser import Parser
from charm.refactor.parsers.fnf import FNFParser
from charm.refactor.parsers.fnfv2 import FNFV2Parser
from charm.refactor.parsers.mania import ManiaParser
from charm.refactor.parsers.sm import SMParser
from charm.refactor.parsers.hero import HeroParser
from charm.refactor.parsers.taiko import TaikoParser

ParserChooser = Callable[[Path], bool]

def get_FNF_version(p: Path) -> int:
    if p.suffix != ".json":
        return 0
    else:
        with open(p, encoding = "utf-8") as f:
            try:
                j = json.load(f)
            except json.JSONDecodeError:
                return 0
            if "version" not in j:
                return 1
            else:
                try:
                    v = int(j["version"].split(".")[0])
                    return v
                except ValueError:
                    return 1

class TypePair(NamedTuple):
    gamemode: str
    filetype: str | ParserChooser

# TODO: Parse MIDI
parser_map: dict[TypePair, type[Parser]] = {
    TypePair('fnf', lambda p: get_FNF_version(p) == 1): FNFParser,
    TypePair('fnf', lambda p: get_FNF_version(p) == 2): FNFV2Parser,
    TypePair('4k', '.osu'): ManiaParser,
    TypePair('4k', '.ssc'): SMParser,
    TypePair('4k', '.sm'): SMParser,
    TypePair('hero', '.chart'): HeroParser,
    TypePair('taiko', '.osu'): TaikoParser
}

def get_needed_parsers(directory: Path, files: list[str]) -> set[Parser]:
    pairs = tuple(parser_map.items())
    found_parsers = []
    for typepair, parser in pairs:
        if isinstance(typepair.filetype, str):
            if any(file.endswith(typepair.filetype) for file in files):
                found_parsers.append(parser)
        else:
            if any(typepair.filetype(directory / file) for file in files):
                found_parsers.append(parser)
    return set(found_parsers)

def load_chartsets() -> list[ChartSet]:
    all_set_paths = (p for p in songspath.glob('**/*') if p.is_dir())
    chartsets = []
    for d in all_set_paths:
        files = [f for f in os.listdir(d) if Path.is_file(d / f)]
        if not files:
           continue
        needed_parsers = get_needed_parsers(d, files)
        charts = []
        for parser in needed_parsers:
            charts.extend(parser.parse_metadata(d))
        if charts:
            chartset = ChartSet(d)
            chartset.charts = charts
            # TODO: Lyric events?
            chartsets.append(chartset)
    return chartsets

def load_chart(chart_metadata: ChartMetadata) -> list[Chart]:
    parsers = get_needed_parsers(chart_metadata.path.parent, [str(chart_metadata.path.relative_to(chart_metadata.path.parent))])
    parser = next(iter(parsers))
    return parser.parse_chart(chart_metadata)
