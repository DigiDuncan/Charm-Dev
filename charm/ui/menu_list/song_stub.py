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
