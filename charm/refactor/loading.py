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

from typing import NamedTuple
from pathlib import Path
import os

from charm.lib.paths import songspath

from charm.refactor.generic.chartset import ChartSet
from charm.refactor.generic.chart import Chart

# -- PARSERS --
from charm.refactor.generic.parser import Parser
from charm.refactor.parsers.fnf import FNFParser
from charm.refactor.parsers.mania import ManiaParser
from charm.refactor.parsers.sm import SMParser
from charm.refactor.parsers.hero import HeroParser
from charm.refactor.parsers.taiko import TaikoParser

class TypePair(NamedTuple):
    gamemode: str
    filetype: str

parser_map: dict[TypePair, type[Parser]] = {
    TypePair('fnf', '.json'): FNFParser,
    TypePair('4k', '.osu'): ManiaParser,
    TypePair('4k', '.ssc'): SMParser,
    TypePair('4k', '.sm'): SMParser,
    TypePair('hero', '.chart'): HeroParser,
    TypePair('taiko', '.osu'): TaikoParser
}
# TODO: parse midi


def load_chartsets() -> list[ChartSet]:
    pairs = tuple(parser_map.items())
    all_set_paths = (p for p in songspath.glob('**/*') if p.is_dir())
    chartsets = []
    for d in all_set_paths:
        files = [f for f in os.listdir(d) if Path.is_file(d / f)]
        if not files:
           continue
        needed_parsers = {parser for typepair, parser in pairs if any(file.endswith(typepair.filetype) for file in files)}
        charts = []
        for parser in needed_parsers:
            print(parser)
            charts.extend(parser.parse_metadata(d))
        chartset = ChartSet(d)
        chartset.charts = charts
        # TODO: Lyric events?
        chartsets.append(chartset)
    return chartsets


def load_chart(chart: Chart) -> list[Chart]:
    gamemode = chart.gamemode
    filetype = chart.path.suffix

    parser = parser_map[TypePair(gamemode, filetype)]
    return parser.parse_chart(chart)

chartsets = load_chartsets()
print(chartsets)
