from __future__ import annotations

from pathlib import Path

from charm.lib.gamemodes.fnf import FNFSong
from charm.lib.paths import songspath
from charm.lib.generic.song import Metadata


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
