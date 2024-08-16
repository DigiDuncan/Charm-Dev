class Metadata:

    def __init__(self, name: str) -> None:
        self.name: str = name

class Chart:
    def __init__(self, gamemode: str, difficulty: str) -> None:
        self.gamemode: str = gamemode
        self.difficulty: str = difficulty

class Song:

    def __init__(self, data: Metadata, charts: list[Chart]) -> None:
        self.data: Metadata = data
        self.charts: list[Chart] = charts

    def __hash__(self) -> int:
        # TODO: Use the actual metadata you stinky. Will be done when connecting to refactor
        return hash(id(self))

    def __eq__(self, value: object) -> bool:
        return id(self) == id(value)
