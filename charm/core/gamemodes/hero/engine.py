from collections import defaultdict

from charm.core.generic.engine import DigitalKeyEvent
from charm.lib.keymap import keymap
from charm.lib.types import Seconds

from charm.core.generic import Engine, EngineEvent, Judgement
from .chart import ChordShape, HeroChart, HeroNote


class ChordShapeChangeEvent(EngineEvent):
    def __init__(self, time: Seconds, chord_shape: ChordShape):
        super().__init__(time)
        self.chord_shape = chord_shape


class HeroEngine(Engine[HeroChart, HeroNote]):
    def __init__(self, chart: HeroChart, offset: Seconds = 0):
        judgements = [
            Judgement('Pass', 'pass', 140, 10, 1),
            Judgement('Miss', 'miss', float('inf'), 0, 0),
        ]
        super().__init__(chart, judgements, offset)

        self.current_events: list[ChordShapeChangeEvent | DigitalKeyEvent] = []
        self.last_event_times = defaultdict(None)

        self.infinite_front_end = False
        self.hopo_leniency: Seconds = 0.080
        self.strum_leniency: Seconds = 0.060
        self.no_note_leniency: Seconds = 0.030

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        if symbol in (keymap.hero.green, keymap.hero.red, keymap.hero.yellow, keymap.hero.blue, keymap.hero.orange):
            self.current_events.append(ChordShapeChangeEvent(self.chart_time, ChordShape(
                keymap.hero.green.held,
                keymap.hero.red.held,
                keymap.hero.yellow.held,
                keymap.hero.blue.held,
                keymap.hero.orange.held
            )))

        elif symbol == keymap.hero.strumup:
            self.current_events.append(DigitalKeyEvent(self.chart_time, "strumup", "down"))
        elif symbol == keymap.hero.strumdown:
            self.current_events.append(DigitalKeyEvent(self.chart_time, "strumdown", "down"))

        self.last_event_times[symbol] = self.chart_time

    def on_key_release(self, symbol: int, modifiers: int) -> None:
        if symbol in (keymap.hero.green, keymap.hero.red, keymap.hero.yellow, keymap.hero.blue, keymap.hero.orange):
            self.current_events.append(ChordShapeChangeEvent(self.chart_time, ChordShape(
                keymap.hero.green.held,
                keymap.hero.red.held,
                keymap.hero.yellow.held,
                keymap.hero.blue.held,
                keymap.hero.orange.held
            )))

            self.last_event_times[symbol] = None

        elif symbol == keymap.hero.strumup:
            self.current_events.append(DigitalKeyEvent(self.chart_time, "strumup", "up"))
        elif symbol == keymap.hero.strumdown:
            self.current_events.append(DigitalKeyEvent(self.chart_time, "strumdown", "up"))
