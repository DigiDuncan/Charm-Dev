from pathlib import Path

import appdirs


def getDataDir():
    appname = "Charm"
    appauthor = "DigiDuncan"
    datadir = Path(appdirs.user_data_dir(appname, appauthor))
    return datadir


# File paths
datadir = getDataDir()
confpath = datadir / "charm.conf"
songspath = datadir / "songs"
scorespath = datadir / "scores.db"
