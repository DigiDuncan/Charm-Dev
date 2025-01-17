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
from operator import attrgetter
import tomllib
from typing import cast
from collections.abc import Iterator, Sequence
from pathlib import Path
from itertools import groupby

from charm.core.paths import songspath
from charm.lib.errors import CharmError, ChartUnparseableError, MissingGamemodeError, NoParserError, AmbigiousParserError, log_charmerror, NoChartsError

from charm.game.generic import ChartSet, ChartSetMetadata, ChartMetadata, Parser, BaseChart
from charm.game.parsers import FNFParser, FNFV2Parser, ManiaParser, SMParser, DotChartParser, TaikoParser

logger = logging.getLogger("charm")

CHARM_TOML_METADATA_FIELDS = ["title", "artist", "album", "length", "genre", "year", "difficulty",
                              "charter", "preview_start", "preview_end", "source", "album_art", "alt_title"]


# TODO: Parse MIDI
all_parsers: list[type[Parser]] = [FNFParser, FNFV2Parser, ManiaParser, SMParser, DotChartParser, TaikoParser]
parsers_by_gamemode: dict[str, list[type[Parser]]] = {
    cast(str, gamemode): list(values)
    for gamemode, values
    in groupby(sorted(all_parsers, key=attrgetter("gamemode")), attrgetter("gamemode"))
}


def get_album_art_path_from_metadata(metadata: ChartSetMetadata) -> str | None:
    # Iterate through frankly too many possible paths for the album art location.
    art_path = None
    # Clone Hero-style (also probably the recommended format.)
    art_paths = [
        metadata.path / "album.png",
        metadata.path / "album.jpg",
        metadata.path / "album.gif"
    ]
    # Stepmania-style
    art_paths.extend(metadata.path.glob("*jacket.png"))
    art_paths.extend(metadata.path.glob("*jacket.jpg"))
    art_paths.extend(metadata.path.glob("*jacket.gif"))
    for p in art_paths:
        if p.is_file():
            art_path = p
            break

    return None if art_path is None else art_path.name


def read_charm_metadata(metadata_src: Path) -> ChartSetMetadata:
    with open(metadata_src, "rb") as f:
        t = tomllib.load(f)
        # Assuming there should be a TOML table called "metadata", pretend it's there but empty if missing
        d = t.get("metadata", {})
        m = {k: v for k, v in d.items() if k in CHARM_TOML_METADATA_FIELDS}
        m["path"] = metadata_src.parent
        return ChartSetMetadata(**m)


def find_chartset_parser(parsers: Sequence[type[Parser]], path: Path) -> type[Parser]:
    valid_parsers = [p for p in parsers if p.is_possible_chartset(path)]
    if not valid_parsers:
        raise NoParserError(str(path))
    if len(valid_parsers) > 1:
        raise AmbigiousParserError(str(path))
    return valid_parsers[0]


def load_path_chartsets(parsers: Sequence[type[Parser]], chartset_path: Path, metadata: ChartSetMetadata, directory_metadata: ChartSetMetadata | None = None) -> ChartSet:
    chartset_metadata = ChartSetMetadata(chartset_path)
    charts = []

    logger.debug(f"Parsing {chartset_metadata.path}")

    parser = find_chartset_parser(parsers, chartset_path)
    parser_metadata = parser.parse_chartset_metadata(chartset_path)
    chartset_metadata = chartset_metadata.update(parser_metadata)
    charts = parser.parse_chart_metadata(chartset_path)

    if not charts:
        raise NoChartsError(str(chartset_path))
    metadata = metadata.update(chartset_metadata)

    if directory_metadata is not None:
        metadata = metadata.update(directory_metadata)

    # Album art injection
    if metadata.album_art is None:
        metadata.album_art = get_album_art_path_from_metadata(metadata)
    return ChartSet(chartset_path, metadata, charts)


def load_path_chartsets_recursive(parsers: Sequence[type[Parser]], chartset_path: Path, metadata: ChartSetMetadata) -> Iterator[ChartSet]:
    charm_metadata_path = (chartset_path / 'charm.toml')
    directory_metadata = None if not charm_metadata_path.exists() else read_charm_metadata(charm_metadata_path)
    try:
        yield load_path_chartsets(parsers, chartset_path, metadata, directory_metadata)
    except CharmError as e:
        # TODO: Put error code here
        log_charmerror(e, False)

    if directory_metadata is not None:
        # When we aren't creating a chartset then we update
        # with the directory metadata, and pass it to sub directories
        metadata = metadata.update(directory_metadata)

    for d in chartset_path.iterdir():
        if not d.is_dir():
            continue
        yield from load_path_chartsets_recursive(parsers, d, metadata)


def load_gamemode_chartsets(gamemode: str) -> list[ChartSet]:
    root = songspath / gamemode
    if not root.exists():
        raise MissingGamemodeError(gamemode=gamemode)
    metadata = ChartSetMetadata(root)
    return list(load_path_chartsets_recursive(parsers_by_gamemode[gamemode], root, metadata))


def load_chartsets() -> list[ChartSet]:
    return []
    gamemodes = ('fnf', '4k', 'hero', 'taiko')
    chartsets = [chartset for gamemode in gamemodes for chartset in load_gamemode_chartsets(gamemode)]
    # Natalie left a list sorting example here.
    # chartsets = sorted(chartsets, key=lambda c: (c.charts[0].gamemode, c.metadata.title))
    return chartsets


def load_chart(chart_metadata: ChartMetadata) -> Sequence[BaseChart]:
    for parser in parsers_by_gamemode[chart_metadata.gamemode]:
        if parser.is_parsable_chart(chart_metadata.path):
            logger.debug(f"Parsing with {parser}")
            return parser.parse_chart(chart_metadata)
    raise ChartUnparseableError(f'chart: {chart_metadata} cannot be parsed by any parser for gamemode {chart_metadata.gamemode}')
