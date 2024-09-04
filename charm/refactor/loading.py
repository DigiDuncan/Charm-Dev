#
# -- CHARTSET AND CHART LOADING --
#
#   Before the unified menu can show the full list
#   Charm needs to find all of the songs and charts.
#   To save time only the song metadata, and bare minimum
#   for each chart is found.
#
#   ! This is currently done per gamemode folder, but if a mod
#   ! in the future wants to mix gamemodes this will need updating.

# NOTE:
#   There are some major complications caused by FNF having two versions
#   which share file type. We also have to work around 4k and taiko both
#   using .osu files. This is solved in the mvp, but if we want chartsets
#   to mix gamemodes in the future we need to solve this issue.
#   FNF makes things harder again because there are also 'erect' versions
#   of some charts which currently means two chartsets from one folder.
#   This breaks a core assumption of Charm.
# * UPDATE:
#   I have un-interwined Erect remixes from their sibling songs in our test data, for now.
#   It may make sense to just tell players that they have to do this;
#   it's not that hard, and it means we don't have to suddenly support
#   "many-chartsets, one-folder" before MVP.
import logging
import tomllib
from typing import NamedTuple, Any
from collections.abc import Callable, Generator
from pathlib import Path

from charm.lib.paths import songspath
from charm.lib.errors import ChartUnparseableError, MissingGamemodeError

from charm.refactor.generic.chartset import ChartSet, ChartSetMetadata
from charm.refactor.generic.chart import Chart, ChartMetadata

# -- PARSERS --
from charm.refactor.generic.parser import Parser
from charm.refactor.parsers.fnf import FNFParser
from charm.refactor.parsers.fnfv2 import FNFV2Parser
from charm.refactor.parsers.mania import ManiaParser
from charm.refactor.parsers.sm import SMParser
from charm.refactor.parsers.hero import HeroParser
from charm.refactor.parsers.taiko import TaikoParser

logger = logging.getLogger("charm")

ParserChooser = Callable[[Path], bool]
CHARM_TOML_METADATA_FIELDS = ["title", "artist", "album", "length", "genre", "year", "difficulty",
                              "charter", "preview_start", "preview_end", "source", "album_art"]

class TypePair(NamedTuple):
    gamemode: str
    filetype: str

# TODO: Parse MIDI
gamemode_parsers: dict[str, tuple[type[Parser], ...]] = {
    'fnf': (FNFParser, FNFV2Parser),
    '4k': (ManiaParser, SMParser),
    'hero': (HeroParser,),
    'taiko': (TaikoParser,)
}

def read_charm_metadata(metadata_src: Path) -> ChartSetMetadata:
    with open(metadata_src, "rb") as f:
        t = tomllib.load(f)
        # Assuming there should be a TOML table called "metadata", pretend it's there but empty if missing
        d = t.get("metadata", {})
        m = {k: v for k, v in d.items() if k in CHARM_TOML_METADATA_FIELDS}
        m["path"] = metadata_src.parent
        return ChartSetMetadata(**m)

def load_path_chartsets(parsers: tuple[type[Parser], ...], path: Path, metadata: ChartSetMetadata) -> Generator[ChartSet, Any, Any]:
    directory_charm_data = None if not (path / 'charm.toml').exists() else read_charm_metadata(path / 'charm.toml')
    directory_metadata = ChartSetMetadata(path)
    charts = []

    for parser in parsers:
        if not parser.is_possible_chartset(path):
            continue
        parser_metadata = parser.parse_chartset_metadata(path)
        directory_metadata = directory_metadata.update(parser_metadata)
        charts.extend(parser.parse_chart_metadata(path))

    if charts:
        metadata = metadata.update(directory_metadata)
        if directory_charm_data is not None:
            metadata = metadata.update(directory_charm_data)
        yield ChartSet(path, metadata, charts)
    metadata = metadata if directory_charm_data is None else metadata.update(directory_charm_data)

    for d in path.iterdir():
        if not d.is_dir():
            continue
        yield from load_path_chartsets(parsers, d, metadata)


def load_gamemode_chartsets(gamemode: str) -> list[ChartSet]:
    parsers = gamemode_parsers[gamemode]
    root = songspath / gamemode
    if not root.exists():
        raise MissingGamemodeError(gamemode=gamemode)
    metadata = ChartSetMetadata(root)
    return list(load_path_chartsets(parsers, root, metadata))


def load_chartsets() -> list[ChartSet]:
    gamemodes = ('fnf', '4k', 'hero', 'taiko')
    chartsets = []
    for gamemode in gamemodes:
        chartsets.extend(load_gamemode_chartsets(gamemode))
    return chartsets


def load_chart(chart_metadata: ChartMetadata) -> list[Chart]:
    parsers = gamemode_parsers[chart_metadata.gamemode]
    for parser in parsers:
        if parser.is_parsable_chart(chart_metadata.path):
            logger.debug(f"Parsing with {parser}")
            return parser.parse_chart(chart_metadata)
    raise ChartUnparseableError(f'chart: {chart_metadata} cannot be parsed by any parser for gamemode {chart_metadata.gamemode}')
