from dataclasses import dataclass

from charm.lib.generic.song import Seconds, Event


@dataclass
class ModchartEvent(Event):
    """A single event in a modchart."""
    fired: bool

@dataclass
class HighwayMoveEvent(ModchartEvent):
    """Move the highway (dx, dy) in t seconds."""
    t: float
    dx: float = 0.0
    dy: float = 0.0

class Modchart:
    def __init__(self, events: list[Event] = None):
        self.current_time: Seconds = 0.0
        self.events: list[ModchartEvent] = events if events else []

    def tick(self, new_time: Seconds) -> list[ModchartEvent]:
        if new_time < self.current_time:
            return []  # Time has gone backwards!

        return [e for e in self.events if self.current_time <= e.time <= new_time and not e.fired]
