from base64 import standard_b64decode, standard_b64encode
from json import dumps, loads
from pathlib import Path
from typing import TypedDict

from charm.lib.generic.results import Results, ScoreJSON

class ScoreDBJSON(TypedDict):
    version: int
    scores: dict[str, ScoreJSON]


class ScoreDB:
    """Decrypt, edit, then encrypt a Base64-encoded JSON of key-value pairs of type (hash: ScoreJSON)."""

    def __init__(self, path: Path):
        self.path = path
        self.version = 0

    @property
    def empty(self) -> ScoreDBJSON:
        return {"version": self.version, "scores": {}}.copy()

    def load(self) -> ScoreDBJSON:
        encrypted: str = None
        if self.path.exists():
            with open(self.path, "r+") as f:
                encrypted = f.read()
            decrypted = standard_b64decode(encrypted)
            scores: ScoreDBJSON = loads(decrypted)
        else:
            scores: ScoreDBJSON = self.empty
        if not encrypted:
            scores: ScoreDBJSON = self.empty
        return scores

    def get_score(self, chart_hash: str) -> ScoreJSON | None:
        scores = self.load()
        if chart_hash in scores["scores"]:
            return scores["scores"][chart_hash]
        return None

    def add_score(self, chart_hash: str, results: Results):
        scores = self.load()
        j = results.to_score_JSON()
        if chart_hash not in scores["scores"]:
            scores["scores"][chart_hash] = j
        elif scores["scores"][chart_hash]["score"] < j["score"]:
            scores["scores"][chart_hash] = j
        json_string = dumps(scores)
        reencrypted = standard_b64encode(bytes(json_string, "utf-8"))
        with open(self.path, "w+") as f:
            f.write(reencrypted.decode())
