from __future__ import annotations

from pathlib import Path

from charm.lib.gamemodes.fnf import FNFSong, FNFChart
from charm.lib.paths import songspath
from charm.lib.generic.song import Metadata

import re
import os


def load_songs_fnf() -> list[Metadata]:
    songs: list[Metadata] = []
    rootdir = Path(songspath / "fnf")
    dir_list = [d for d in rootdir.glob('**/*') if d.is_dir()]
    for d in dir_list:
        k = d.name
        for diff, suffix in [("expert", "-ex"), ("hard", "-hard"), ("normal", ""), ("easy", "-easy")]:
            if (d / f"{k}{suffix}.json").exists():
                songdata = FNFSong.get_metadata(d)
                songs.append(songdata)
                break
    return songs


def load_songs_and_chart_stub_fnf() -> list[FNFSong]:
    songs: list[FNFSong] = []
    rootdir = Path(songspath / "fnf")
    dir_list = [d for d in rootdir.glob('**/*') if d.is_dir()]
    for d in dir_list:
        expression = re.escape(d.name.casefold()) + r'(\-.*)?\.json'
        chart_srcs = (f for f in os.listdir(d) if re.match(expression, f.casefold()) is not None)

        chart_srcs = tuple(chart_srcs)
        # TODO: This should warn if the folder is empty
        if not chart_srcs:
            continue

        song = FNFSong(d)
        song.metadata = Metadata(path=d, title=d.stem.replace("-", " ").title(), gamemode='fnf', hash=f'fnf-{d.name}')
        song.charts = [FNFChart(song, chart.casefold().split('.')[0].removeprefix(d.name.casefold()).removeprefix('-') or 'normal', 1, 0.0, f'fnf-{chart.split('.')[0]}') for chart in chart_srcs]
        songs.append(song)
    return songs
