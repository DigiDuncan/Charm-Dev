from typing import cast
import logging
import math
from statistics import mean

from arcade.clock import GLOBAL_CLOCK

from charm.lib.keymap import Action, keymap
from charm.lib.types import Range4, Seconds
from charm.lib.utils import clamp

from charm.core.generic import Engine, Judgement, DigitalKeyEvent, Results, BaseResults
from .chart import FourKeyChart, FourKeyNote, FourKeyNoteType

logger = logging.getLogger("charm")

# !: Should SMEngine exist?
# FourKeyEngine is probably a better idea, but same with the SMParser, this thing
# relies heavily on the simfile library's TimingEngine and frankly would require
# a lot of rewriting to not do that.
# Oh well!
# * EDIT: This got renamed to FourKeyEngine, but didn't fundamentally change!
# * aaaaaaaa
# ?: OK, what the f***. This code doesn't rely on TimingEngine at all, I think
# only the SMParser does. Why this comment was ever here remains a mystery.
# I'm leaving this here for now because stupidity and confusion of this level
# deserves to be documented.
# !: TO REITERATE: THIS IS FINE. FourKeyEngine doesn't rely on simfile and possibly never has.
class FourKeyEngine(Engine[FourKeyChart, FourKeyNote]):
    def __init__(self, chart: FourKeyChart, offset: Seconds = 0):  # TODO: Set this dynamically
        judgements = [
            #        ("name",           "key"             ms, score, acc, hp=0)
            Judgement("Super Charming", "supercharming",  10, 1000, 1.0, 0.04),
            Judgement("Charming",       "charming",       25, 1000, 0.9, 0.04),
            Judgement("Excellent",      "excellent",      35, 800,  0.8, 0.03),
            Judgement("Great",          "great",          45, 600,  0.7, 0.02),
            Judgement("Good",           "good",           60, 400,  0.6, 0.01),
            Judgement("OK",             "ok",             75, 200,  0.5),
            Judgement("Miss",           "miss",     math.inf,   0,    0, -0.1)
        ]
        super().__init__(chart, judgements, offset)

        self.min_hp = 0
        self.hp = 1
        self.max_hp = 2
        self.bomb_hp = 0.5

        self.has_died = False

        self.latest_judgement = None
        self.latest_judgement_time = None
        self.all_judgements: list[tuple[Seconds, Seconds, Judgement]] = []

        self.current_events: list[DigitalKeyEvent[Range4]] = []

        self.last_p1_action: Action | None = None
        self.last_note_missed = False
        self.streak = 0
        self.max_streak = 0

        # ! This might not be the right way to do this nor accurate to how most games handle this!
        self.sustain_score_per_sec = self.judgements[0].score
        self.miss_on_sustain_break = True

        self.active_sustains: list[FourKeyNote] = []
        self.keystate: tuple[bool, bool, bool, bool] = (False, False, False, False)

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        self.keystate = keymap.fourkey.state
        # ignore spam during front/back porch
        if (self.chart_time < self.chart.notes[0].time - self.hit_window \
           or self.chart_time > self.chart.notes[-1].time + self.hit_window):
            return
        action = keymap.fourkey.pressed_action
        if action is None:
            return
        key = cast(Range4, keymap.fourkey.actions.index(action))
        self.current_events.append(DigitalKeyEvent(self.chart_time, key, "down"))

    def on_key_release(self, symbol: int, modifiers: int) -> None:
        self.keystate = keymap.fourkey.state
        if self.last_p1_action is not None and not self.last_p1_action.held:
            self.last_p1_action = None
        # ignore spam during front/back porch
        if (self.chart_time < self.chart.notes[0].time - self.hit_window \
           or self.chart_time > self.chart.notes[-1].time + self.hit_window):
            return
        action = keymap.fourkey.released_action
        if action is None:
            return
        key = cast(Range4, keymap.fourkey.actions.index(action))
        self.current_events.append(DigitalKeyEvent(self.chart_time, key, "up"))

    @property
    def average_acc(self) -> float:
        j = [j[1] for j in self.all_judgements if j[1] is not math.inf]
        return mean(j) if j else 0

    def calculate_score(self) -> None:
        # Get all non-scored notes within the current window
        for note in (n for n in self.current_notes if n.time <= self.chart_time + self.hit_window):
            # Get sustains in the window and add them to the active sustains list
            if note.is_sustain and note not in self.active_sustains:
                self.active_sustains.append(note)
            # Missed notes (current time is higher than max allowed time for note)
            if self.chart_time > note.time + self.hit_window:
                note.missed = True
                note.hit_time = math.inf  # how smart is this? :thinking:
                self.score_note(note)
                self.current_notes.remove(note)
            else:
                # Check non-used events to see if one matches our note
                for event in (e for e in self.current_events if e.new_state == "down"):
                    # We've determined the note was hit
                    if event.key == note.lane and abs(event.time - note.time) <= self.hit_window:
                        note.hit = True
                        note.hit_time = event.time
                        self.score_note(note)
                        try:
                            self.current_notes.remove(note)
                        except ValueError:
                            logger.info("Note removal failed!")
                        self.current_events.remove(event)
                        self.last_note_hit = note
                        break

        for sustain in self.active_sustains:
            if self.chart_time > sustain.end + self.hit_window:
                self.active_sustains.remove(sustain)

        # Check sustains
        self.score_sustains()

        # Make sure we can't go below min_hp or above max_hp
        self.hp = clamp(self.min_hp, self.hp, self.max_hp)
        if self.hp == self.min_hp:
            self.has_died = True

        self.last_score_check = self.chart_time

    def score_note(self, note: FourKeyNote) -> None:
        # Ignore notes we haven't done anything with yet
        if not (note.hit or note.missed):
            return

        # Bomb notes penalize HP when hit
        if note.type == FourKeyNoteType.BOMB:
            if note.hit:
                self.hp -= self.bomb_hp
            return

        # Score the note
        j = self.get_note_judgement(note)
        self.score += j.score
        self.weighted_hit_notes += j.accuracy_weight

        # Judge the player
        rt = note.hit_time - note.time  # type: ignore -- the type checker is stupid, clearly this isn't ever None at this point
        self.latest_judgement = j
        self.latest_judgement_time = self.chart_time
        self.all_judgements.append((self.latest_judgement_time, rt, self.latest_judgement))

        # Animation and hit/miss tracking
        self.last_p1_action = keymap.fourkey.actions[note.lane]
        if note.missed:
            self.misses += 1
            self.streak = 0
            self.last_note_missed = True
        else:
            self.hits += 1
            self.streak += 1
            self.max_streak = max(self.streak, self.max_streak)
            self.last_note_missed = False

            # We just hit a sustain, get it set as active:
            if note.is_sustain and note not in self.active_sustains:
                self.active_sustains.append(note)

    def score_sustains(self) -> None:
        dt = GLOBAL_CLOCK.dt

        kill = []
        for sustain in self.active_sustains:
            if self.keystate[sustain.lane]:
                self.score += self.sustain_score_per_sec * dt
            else:
                if self.miss_on_sustain_break:
                    self.streak = 0
                kill.append(sustain)
        self.active_sustains = [s for s in self.active_sustains if s not in kill]

    def generate_results(self) -> BaseResults:
        return Results(
            self.chart,
            self.hit_window,
            self.judgements,
            self.all_judgements,
            self.score,
            self.hits,
            self.misses,
            self.accuracy,
            self.grade,
            self.fc_type,
            self.streak,
            self.max_streak
        )
