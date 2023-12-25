from dataclasses import dataclass
import typing
from charm.lib.anim import ease_linear

from charm.lib.generic.song import Seconds, Event

if typing.TYPE_CHECKING:
    from charm.views.fourkeysong import FourKeySongView


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

class ModchartProcessor:
    def __init__(self, modchart: Modchart, view: "FourKeySongView"):
        self.modchart = modchart
        self.view = view

        self._active_highway_moves = []

    def process_modchart(self):
        # Get events
        current_modevents = self.modchart.tick(self.view.tracks.time)

        # Convert events into frame-events? I don't know what to call these
        for e in current_modevents:
            if isinstance(e, HighwayMoveEvent):
                self._active_highway_moves.append(
                    {"start_x": self.view.highway.x, "start_y": self.view.highway.y,
                     "end_x": self.view.highway.x + e.dx, "end_y": self.view.highway.y + e.dy,
                     "start_time": e.time, "end_time": e.time + e.t}
                )
            e.fired = True

        # Excecute highway moves
        if self._active_highway_moves:
            for move in self._active_highway_moves:
                self.view.highway.x = ease_linear(move["start_x"], move["end_x"], move["start_time"], move["end_time"], self.view.tracks.time)
                self.view.highway.y = ease_linear(move["start_y"], move["end_y"], move["start_time"], move["end_time"], self.view.tracks.time)

                if move["end_time"] < self.view.tracks.time:
                    self._active_highway_moves.remove(move)
