from base64 import standard_b64decode, standard_b64encode
from json import dumps, loads
from pathlib import Path
from typing import TypedDict

class ScoreJSON(TypedDict):
    version: int
    scores: dict[str, int]


class ScoreDB:
    """Decrypt, edit, then encrypt a Base64-encoded JSON of key-value pairs of type (hash: score)."""

    def __init__(self, path: Path):
        self.path = path
        self.version = 0

    def add_score(self, chart_hash: str, score: int):
        encrypted: str = None
        if self.path.exists():
            with open(self.path, "r+") as f:
                encrypted = f.read()
            decrypted = standard_b64decode(encrypted)
            scores: ScoreJSON = loads(decrypted)
        else:
            scores: ScoreJSON = {"version": self.version, "scores": {}}
        if not encrypted:
            scores: ScoreJSON = {"version": self.version, "scores": {}}
        if chart_hash not in scores["scores"] or score["scores"][chart_hash] < score:
            scores["scores"][chart_hash] = score
        json_string = dumps(scores)
        reencrypted = standard_b64encode(bytes(json_string, "utf-8"))
        with open(self.path, "w+") as f:
            f.write(reencrypted.decode())
