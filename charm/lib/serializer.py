import json
from pathlib import Path
from charm.lib.generic.song import Chart

def serialize(chart: Chart, path: Path = Path("./serialized.json")) -> None:
    output = []
    for note in chart.notes:
        if note.type != "sustain":
            output.append({"time": note.time, "lane": note.lane, "length": note.length, "type": note.type})

    with open(path, "w") as f:
        json.dump(output, f, indent = 4)
