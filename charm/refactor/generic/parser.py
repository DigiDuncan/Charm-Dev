from pathlib import Path
from charm.refactor.generic import Chart

class Parser[T: Chart]:
    def __init__(self, path: Path) -> None:
        self.path = path

    def parse(self) -> list[T]:
        raise NotImplementedError
