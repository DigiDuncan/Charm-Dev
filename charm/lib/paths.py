from pathlib import Path

import appdirs


def _get_data_dir():
    appname = "Charm"
    appauthor = "DigiDuncan"
    datadir = Path(appdirs.user_data_dir(appname, appauthor))
    return datadir


# File paths
datadir = _get_data_dir()
confpath = datadir / "charm.conf"
songspath = datadir / "songs"
scorespath = datadir / "scores.db"

fnfpath = songspath / "fnf"
fourkeypath = songspath / "4k"
taikopath = songspath / "taiko"
heropath = songspath / "hero"

datadir.mkdir(parents=True, exist_ok=True)
songspath.mkdir(parents=True, exist_ok=True)
fnfpath.mkdir(parents=True, exist_ok=True)
fourkeypath.mkdir(parents=True, exist_ok=True)
taikopath.mkdir(parents=True, exist_ok=True)
heropath.mkdir(parents=True, exist_ok=True)
