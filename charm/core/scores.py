from base64 import standard_b64decode, standard_b64encode
from json import dumps, loads
import logging
from pathlib import Path
from typing import TypedDict
from charm.lib.errors import ScoreDBVersionMismatchError

from charm.lib.generic.results import Results, ScoreJson

logger = logging.getLogger("charm")

CURRENT_VERSION = 0


class ScoreDBJSON(TypedDict):
    version: int
    scores: dict[str, list[ScoreJson]]


class ScoreDB:
    """Decrypt, edit, then encrypt a Base64-encoded JSON of key-value pairs of type (hash: ScoreJSON)."""

    def __init__(self, path: Path):
        self.path = path
        self.version = CURRENT_VERSION

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
            if scores["version"] != CURRENT_VERSION:
                raise ScoreDBVersionMismatchError(scores["version"], CURRENT_VERSION)
            logger.debug("Loading score DB...")
        else:
            scores: ScoreDBJSON = self.empty
            logger.debug("Creating new score DB...")
        if not encrypted:
            scores: ScoreDBJSON = self.empty
            logger.debug("Creating new score DB...")
        return scores

    def get_scores(self, chart_hash: str | None) -> list[ScoreJson]:
        if chart_hash is None:
            return []
        scores = self.load()
        if chart_hash in scores["scores"]:
            return scores["scores"][chart_hash]
        return []

    def get_best_score(self, chart_hash: str | None) -> ScoreJson | None:
        if chart_hash is None:
            return None
        scores = self.load()
        if chart_hash in scores["scores"]:
            l = scores["scores"][chart_hash]
        else:
            return None
        return max(l, key = "score")

    def add_score(self, chart_hash: str | None, results: Results) -> None:
        if chart_hash is None:
            return
        scores = self.load()
        j = results.to_score_json()
        if chart_hash not in scores["scores"]:
            scores["scores"][chart_hash] = []
        scores["scores"][chart_hash].append(j)
        json_string = dumps(scores)
        reencrypted = standard_b64encode(bytes(json_string, "utf-8"))
        with self.path.open("w+") as f:
            f.write(reencrypted.decode())
        logger.debug(f"Wrote new score to score DB for hash '{chart_hash}'!")
