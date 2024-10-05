from typing import Literal, cast
import logging
import math

from charm.lib.keymap import Action, keymap, KeyMap
from charm.lib.types import Range4, Seconds
from charm.lib.utils import clamp

from charm.core.generic import DigitalKeyEvent, Engine, Judgement, Results, BaseResults
from charm.core.gamemodes.four_key import FourKeyNoteType, FourKeyNote, FourKeyChart

logger = logging.getLogger("charm")

class FNFEngine(Engine[FourKeyChart, FourKeyNote]):
    def __init__(self, chart: FourKeyChart, offset: Seconds = 0):
        judgements = [
            #        ("name",  "key"    ms,       score, acc,   hp=0)
            Judgement("sick",  "sick",  45,       350,   1,     0.04),
            Judgement("good",  "good",  90,       200,   0.75),
            Judgement("bad",   "bad",   135,      100,   0.5,  -0.03),
            Judgement("awful", "awful", 166,      50,    -1,   -0.06),  # I'm not calling this "s***", it's not funny.
            Judgement("miss",  "miss",  math.inf, 0,     -1,   -0.1)
        ]
        super().__init__(chart, judgements, offset)

        self.min_hp = 0
        self.hp = 1
        self.max_hp = 2
        self.bomb_hp = 0.5
        self.heal_hp = 0.25

        self.has_died = False

        self.latest_judgement = None
        self.latest_judgement_time = None
        self.all_judgements: list[tuple[Seconds, Seconds, Judgement]] = []

        self.current_events: list[DigitalKeyEvent[Range4]] = []

        self.last_p1_action: Action | None = None
        self.last_note_missed = False
        self.streak = 0
        self.max_streak = 0

        self.active_sustains: list[FourKeyNote] = []
        self.last_sustain_tick = 0
        self.keystate: tuple[bool, bool, bool, bool] = (False, False, False, False)

    def on_button_press(self, keymap: KeyMap) -> None:
        self.keystate = keymap.fourkey.state
        # ignore spam during front/back porch
        if (self.chart_time < self.chart.notes[0].time - self.hit_window \
           or self.chart_time > self.chart.notes[-1].time + self.hit_window):
            return
        action = keymap.fourkey.pressed_action
        if action is None:
            return
        key = cast(Literal[0, 1, 2, 3], keymap.fourkey.actions.index(action))
        self.current_events.append(DigitalKeyEvent(self.chart_time, key, "down"))

    def on_button_release(self, keymap: KeyMap) -> None:
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
        key = cast(Literal[0,1,2,3], keymap.fourkey.actions.index(action))
        self.current_events.append(DigitalKeyEvent(self.chart_time, key, "up"))

    def calculate_score(self) -> None:
        # Get all non-scored notes within the current window
        for note in self.current_notes:
            if note.time > self.chart_time + self.hit_window:
                continue
            # Missed notes (current time is higher than max allowed time for note)
            if note.time < self.chart_time - self.hit_window:
                note.missed = True
                note.hit_time = math.inf
                self.score_note(note)
                self.current_notes.remove(note)
            else:
                if note.type == FourKeyNoteType.SUSTAIN:
                    # Sustain notes just require the right key is held down, and don't "use" an event.
                    if self.keystate[note.lane]:
                        note.hit = True
                        note.hit_time = note.time
                        self.score_note(note)
                        self.current_notes.remove(note)
                # Check non-used events to see if one matches our note
                down_events = (e for e in self.current_events if e.new_state == "down")
                for event in down_events:
                    # We've determined the note was hit
                    if event.key == note.lane and abs(event.time - note.time) <= self.hit_window:
                        note.hit = True
                        note.hit_time = event.time
                        self.score_note(note)
                        try:
                            self.current_notes.remove(note)
                        except ValueError:
                            logger.info("Sustain pickup failed!")  # TODO: I don't know why this happens still, but it does. Often.
                        self.current_events.remove(event)
                        self.last_note_hit = note
                        break

        # Make sure we can't go below min_hp or above max_hp
        self.hp = clamp(self.min_hp, self.hp, self.max_hp)
        if self.hp == self.min_hp:
            self.has_died = True

    def score_note(self, note: FourKeyNote) -> None:
        # Ignore notes we haven't done anything with yet
        if not (note.hit or note.missed):
            return

        # Sustains use different scoring
        if note.type == FourKeyNoteType.SUSTAIN:
            self.last_p1_action = keymap.fourkey.actions[note.lane]
            if note.hit:
                self.hp += 0.02
                self.last_note_missed = False
            elif note.missed:
                self.hp -= 0.05
                self.last_note_missed = True
            return

        # Death notes set HP to minimum when hit
        if note.type == FourKeyNoteType.DEATH and note.hit:
            self.hp = self.min_hp
            return

        # Bomb notes penalize HP when hit
        if note.type == FourKeyNoteType.BOMB and note.hit:
            self.hp -= self.bomb_hp
            return

        # Score the note
        j = self.get_note_judgement(note)
        self.score += j.score
        self.weighted_hit_notes += j.accuracy_weight

        # Give HP for hit note (heal notes give more)
        if note.type == FourKeyNoteType.HEAL and note.hit:
            self.hp += self.heal_hp
        elif note.hit:
            self.hp += j.hp_change

        # Judge the player
        rt = note.hit_time - note.time  # type: ignore -- the type checker is stupid, clearly this isn't ever None at this point
        self.latest_judgement = j
        self.latest_judgement_time = self.chart_time
        self.all_judgements.append((self.latest_judgement_time, rt, self.latest_judgement))

        # Animation and hit/miss tracking
        self.last_p1_action = keymap.fourkey.actions[note.lane]
        if note.missed:
            self.misses += 1
            self.max_streak = max(self.streak, self.max_streak)
            self.streak = 0
            self.last_note_missed = True
        else:
            self.hits += 1
            self.streak += 1
            self.last_note_missed = False

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
