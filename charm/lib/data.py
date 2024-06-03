from pathlib import Path
import appdirs
import json


appname = "Charm"
appauthor = "DigiDuncan"
datadir = Path(appdirs.user_data_dir(appname, appauthor))

def save(key: str, data: object) -> None:
    p = datadir / key
    with p.open("w") as f:
        json.dump(data, f)

def load(key: str) -> object:
    p = datadir / key
    with p.open("r") as f:
        data = json.load(f)
    return data
