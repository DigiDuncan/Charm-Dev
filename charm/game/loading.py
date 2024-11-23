"""
Threaded chart loading Oh lorde what have I done ~ DragonMoffon
"""
import logging
from operator import attrgetter
import tomllib
from typing import cast
from collections.abc import Iterator, Sequence
from pathlib import Path
from itertools import groupby
from queue import Queue
from threading import Thread, Lock

from charm.core.paths import songspath
from charm.lib.errors import CharmError, ChartUnparseableError, MissingGamemodeError, NoParserError, AmbigiousParserError, log_charmerror, NoChartsError

from charm.game.generic import ChartSet, ChartSetMetadata, ChartMetadata, Parser, BaseChart
from charm.game.parsers import FNFParser, FNFV2Parser, ManiaParser, SMParser, DotChartParser, TaikoParser

from time import sleep

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

class ThreadError(Exception):
    pass

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
        raise ThreadError(f'NoParserError: {path}')
    if len(valid_parsers) > 1:
        raise ThreadError(f'AmbigiousParserError: {path}')
    return valid_parsers[0]


class ChartLoader:
    """
    The class that manages the threaded chart loading functionality.
    """

    def __init__(self) -> None:
        self._chartsets: list[ChartSet] = []
        self._free_chartsets: list[ChartSet] = []
        self._grown: bool = False
        self._finished: bool = False

        self._grown_lock: Lock = Lock()
        self._finished_lock: Lock = Lock()
        self._chartset_lock: Lock = Lock()

        self._loading_thread: Thread = None

        # TODO
        self._chartset_counts: dict[str, int] = {}
        self._chartsets_to_process: int = 0
        self._chartsets_processed: int = 0
        self._gamemode_map: dict[str, list[ChartSet]] = {}


    # Main thread ONLY methods
    def wake_loader(self) -> None:
        # Create the charset loading thread.
        self._loading_thread = Thread(target=self.load_chartsets, name='chart_loader')

    def start_loading(self) -> None:
        if not self.is_awake:
            raise CharmError(title='FATAL', message='ChartLoader has not been woken')

        if self.is_finished:
            raise CharmError(title='FATAL', message='ChartLoader is finished, this is a TODO to add in chaching')
        self._loading_thread.start()

    @property
    def is_awake(self) -> bool:
        return self._loading_thread is not None

    @property
    def is_finished(self) -> bool:
        with self._finished_lock:
            return self._finished

    def copy_chartsets(self) -> list[ChartSet]:
        with self._grown_lock:
            if not self._grown:
                return self._free_chartsets
            self._grown = False

        with self._chartset_lock:
            self._free_chartsets = self._chartsets[:]

        return self._free_chartsets

    def is_up_to_date(self, test_set: list[ChartSet]) -> bool:
        with self._chartset_lock:
            return test_set is self._free_chartsets

    def load_chartsets(self) -> None:
        gamemodes = ('fnf', '4k', 'hero', 'taiko')
        for gamemode in gamemodes:
            self._load_gamemode_chartsets(gamemode)

        with self._finished_lock:
            self._finished = True

        with self._chartset_lock:
            self._free_chartsets = self._chartsets[:]
        # Natalie left a list sorting example here.
        # chartsets = sorted(chartsets, key=lambda c: (c.charts[0].gamemode, c.metadata.title))

    # Loading thread ONLY methods
    def _add_chartset(self, chartset: ChartSet) -> None:
        with self._chartset_lock:
            self._chartsets.append(chartset)

        with self._grown_lock:
            self._grown = True

    def _load_path_chartsets(self, parsers: Sequence[type[Parser]], chartset_path: Path, metadata: ChartSetMetadata, directory_metadata: ChartSetMetadata | None = None):
        chartset_metadata = ChartSetMetadata(chartset_path)
        charts = []

        logger.debug(f"Parsing {chartset_metadata.path}")

        parser = find_chartset_parser(parsers, chartset_path)
        parser_metadata = parser.parse_chartset_metadata(chartset_path)
        chartset_metadata = chartset_metadata.update(parser_metadata)
        charts = parser.parse_chart_metadata(chartset_path)

        if not charts:
            raise ThreadError("NoChartsError: " + str(chartset_path))  # NoChartsError(str(chartset_path))
        metadata = metadata.update(chartset_metadata)

        if directory_metadata is not None:
            metadata = metadata.update(directory_metadata)

        # Album art injection
        if metadata.album_art is None:
            metadata.album_art = get_album_art_path_from_metadata(metadata)
        self._add_chartset(ChartSet(chartset_path, metadata, charts))

    def _load_path_chartsets_recursive(self, parsers: Sequence[type[Parser]], chartset_path: Path, metadata: ChartSetMetadata):
        charm_metadata_path = (chartset_path / 'charm.toml')
        directory_metadata = None if not charm_metadata_path.exists() else read_charm_metadata(charm_metadata_path)
        try:
            self._load_path_chartsets(parsers, chartset_path, metadata, directory_metadata)
        except ThreadError as e:
            logger.error(e)
            # TODO: Put error code here
            # log_charmerror(e, False)

        if directory_metadata is not None:
            # When we aren't creating a chartset then we update
            # with the directory metadata, and pass it to sub directories
            metadata = metadata.update(directory_metadata)

        for d in chartset_path.iterdir():
            if not d.is_dir():
                continue
            self._load_path_chartsets_recursive(parsers, d, metadata)

    def _load_gamemode_chartsets(self, gamemode: str) -> None:
        root = songspath / gamemode
        if not root.exists():
            raise ThreadError(f'MissingGamemodeError: {gamemode}')
        metadata = ChartSetMetadata(root)
        self._load_path_chartsets_recursive(parsers_by_gamemode[gamemode], root, metadata)


CHART_LOADER = ChartLoader()

def load_chart(chart_metadata: ChartMetadata) -> Sequence[BaseChart]:
    for parser in parsers_by_gamemode[chart_metadata.gamemode]:
        if parser.is_parsable_chart(chart_metadata.path):
            logger.debug(f"Parsing with {parser}")
            return parser.parse_chart(chart_metadata)
    raise ChartUnparseableError(f'chart: {chart_metadata} cannot be parsed by any parser for gamemode {chart_metadata.gamemode}')
