from __future__ import annotations

from typing import Literal, cast
from dataclasses import dataclass
import logging
import math

from charm.core.generic.engine import DigitalKeyEvent, Engine, Judgement, EngineEvent
from charm.core.generic.chart import Seconds
from charm.core.gamemodes.hero import HeroChord, HeroChart, HeroNote
from charm.lib.keymap import Action, keymap

logger = logging.getLogger("charm")


@dataclass
class StrumEvent(EngineEvent):
    action: Action
    shape: list[bool]

    def __str__(self) -> str:
        strum_name = {
            keymap.hero.strumup: "up",
            keymap.hero.strumup: "down"
        }
        return f"<StrumEvent {strum_name[self.action]} @ {round(self.time, 3)}: {[n for n, v in enumerate(self.shape) if v is True]}>"


FRET_ACTIONS = (keymap.hero.green, keymap.hero.red, keymap.hero.yellow, keymap.hero.blue, keymap.hero.orange)
STRUM_ACTIONS = (keymap.hero.strumup, keymap.hero.strumdown)
POWER_ACTIONS = (keymap.hero.power,)


class HeroEngine(Engine[HeroChart, HeroNote]):
    def __init__(self, chart: HeroChart, offset: Seconds = 0):
        hit_window = 0.050  # 50ms +/-
        judgements = [Judgement("pass", 50, 100, 1, 1), Judgement("miss", math.inf, 0, 0, -1)]

        super().__init__(chart, hit_window, judgements, offset)

        self.current_chords: list[HeroChord] = self.chart.chords.copy()
        self.current_events: list[DigitalKeyEvent[Literal[0, 1, 2, 3, 4, 5, 6, 7]]] = []

        self.combo = 0
        self.star_power = False
        self.strum_events: list[StrumEvent] = []

        self.tap_available = True

    @property
    def current_holds(self) -> list[bool]:
        return keymap.hero.state

    @property
    def multiplier(self) -> int:
        base = min(((self.combo // 10) + 1), 4)
        return base * 2 if self.star_power else base

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        # ignore spam during front/back porch
        if (self.chart_time < self.chart.notes[0].time - self.hit_window
           or self.chart_time > self.chart.notes[-1].time + self.hit_window):
            return
        action = keymap.hero.pressed_action
        if action is None:
            return
        # pressed
        key = cast(Literal[0,1,2,3,4,5,6,7], keymap.hero.actions.index(action))
        self.current_events.append(DigitalKeyEvent(self.chart_time, key, "down"))
        if action in FRET_ACTIONS:
            # fret button
            self.tap_available = True
        elif action in STRUM_ACTIONS:
            # strum button
            self.strum_events.append(StrumEvent(self.chart_time, action, self.current_holds))
        elif action in POWER_ACTIONS:
            # power button
            pass

    def on_key_release(self, symbol: int, modifiers: int) -> None:
        # ignore spam during front/back porch
        if (self.chart_time < self.chart.notes[0].time - self.hit_window
           or self.chart_time > self.chart.notes[-1].time + self.hit_window):
            return
        action = keymap.hero.released_action
        if action is None:
            return
        key = cast(Literal[0,1,2,3,4,5,6,7], keymap.hero.actions.index(action))
        self.current_events.append(DigitalKeyEvent(self.chart_time, key, "up"))
        if action in FRET_ACTIONS:
            # fret button
            self.tap_available = True

    def calculate_score(self) -> None:
        # CURRENTLY MISSING:
        # Sutains
        # Sustain drops
        # Overstrums
        # Strum leniency

        # Get all strums within the window
        look_at_strums = [e for e in self.strum_events if self.chart_time - self.hit_window <= e.time <= self.chart_time + self.hit_window]

        for chord in self.current_chords:
            if chord.time > self.chart_time + self.hit_window:
                # Since the chords are time sorted we can break
                # once outside the window
                break

            # Strums or HOPOs in strum mode
            if chord.type == "normal" or (chord.type == "hopo" and self.combo == 0):
                self.process_strum(chord, look_at_strums)
            elif chord.type == "hopo" or chord.type == "tap":
                self.process_tap(chord, look_at_strums)

        # Missed chords
        for chord in self.current_chords:
            if chord.time >= self.chart_time - self.hit_window:
                break
            self.process_missed(chord)

        overstrums = [e for e in self.strum_events if self.chart_time > e.time + self.hit_window]

        for strum in self.strum_events:
            if strum.time <= self.chart_time - self.hit_window:
                break

            logger.info(f"Overstrum! ({round(strum.time, 3)})")
            self.combo = 0
            for o in overstrums:
                self.strum_events.remove(o)

    def process_strum(self, chord: HeroChord, strum_events: list[StrumEvent]) -> None:
        for event in strum_events:
            if event.shape in chord.valid_shapes:
                chord.hit = True
                chord.hit_time = event.time
                self.score_chord(chord)
                self.current_chords.remove(chord)
                self.strum_events.remove(event)

    def process_tap(self, chord: HeroChord, strum_events: list[StrumEvent]) -> None:
        if self.current_holds in chord.valid_shapes and self.tap_available:
            chord.hit = True
            chord.hit_time = self.chart_time
            self.score_chord(chord)
            self.current_chords.remove(chord)
            self.tap_available = False
        else:
            self.process_strum(chord, strum_events)

    def process_missed(self, chord: HeroChord) -> None:
        chord.missed = True
        chord.hit_time = math.inf
        self.score_chord(chord)
        self.current_chords.remove(chord)

    def score_chord(self, chord: HeroChord) -> None:
        if chord.hit:
            self.score += 50 * self.multiplier
            self.combo += 1
        elif chord.missed:
            self.combo = 0
