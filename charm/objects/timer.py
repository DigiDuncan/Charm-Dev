class Timer:
    def __init__(self, total_time: float, start_time: float = 0, paused = False):
        self.start_time = start_time
        self.total_time = total_time

        self.current_time = start_time
        self.paused = paused

    @property
    def percentage(self) -> float:
        return self.current_time / self.total_time

    @property
    def current_seconds(self) -> float:
        return self.current_time % 60

    @property
    def current_minutes(self) -> int:
        return self.current_time // 60

    @property
    def total_seconds(self) -> float:
        return self.total_time % 60

    @property
    def total_minutes(self) -> int:
        return self.total_time // 60

    @property
    def display_string(self) -> str:
        return f"{self.current_minutes:d}:{self.current_seconds:02d} / {self.total_minutes:d}:{self.total_seconds:02d}"

    def update(self, delta_time: float):
        if not self.paused:
            self.current_time += delta_time

    def draw(self):
        pass
