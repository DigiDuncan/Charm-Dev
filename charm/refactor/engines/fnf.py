import logging
import math
from charm.lib.keymap import keymap
from charm.lib.types import Seconds
from charm.lib.utils import clamp
from charm.refactor.generic import Engine, Judgement


logger = logging.getLogger("charm")

class FNFEngine(Engine[FNFChart]):
    def __init__(self, chart: FNFChart, offset: Seconds = 0):
        hit_window = 0.166
        judgements = [
            #        ("name",  "key"    ms,       score, acc,   hp=0)
            Judgement("sick",  "sick",  45,       350,   1,     0.04),
            Judgement("good",  "good",  90,       200,   0.75),
            Judgement("bad",   "bad",   135,      100,   0.5,  -0.03),
            Judgement("awful", "awful", 166,      50,    -1,   -0.06),  # I'm not calling this "s***", it's not funny.
            Judgement("miss",  "miss",  math.inf, 0,     -1,   -0.1)
        ]
        super().__init__(chart, offset)
        self.hit_window = hit_window
        self.judgements = judgements

    def calculate_score(self) -> None:
        # Get all non-scored notes within the current window
        for note in [n for n in self.current_notes if n.time <= self.chart_time + self.hit_window]:
            # Missed notes (current time is higher than max allowed time for note)
            if self.chart_time > note.time + self.hit_window:
                note.missed = True
                note.hit_time = math.inf
                self.score_note(note)
                self.current_notes.remove(note)
            else:
                if note.type == "sustain":
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
                        break

        # Make sure we can't go below min_hp or above max_hp
        self.hp = clamp(self.min_hp, self.hp, self.max_hp)
        if self.hp == self.min_hp:
            self.has_died = True

    def score_note(self, note: FNFNote) -> None:
        # Ignore notes we haven't done anything with yet
        if not (note.hit or note.missed):
            return

        # Sustains use different scoring
        if note.type == "sustain":
            self.last_p1_action = keymap.fourkey.actions[note.lane]
            if note.hit:
                self.hp += 0.02
                self.last_note_missed = False
            elif note.missed:
                self.hp -= 0.05
                logger.debug(f"HP lost (note missed, {note}), new HP {self.hp}")
                self.last_note_missed = True
            return

        # Death notes set HP to minimum when hit
        if note.type == "death":
            if note.hit:
                self.hp = self.min_hp
            return

        # Bomb notes penalize HP when hit
        if note.type == "bomb":
            if note.hit:
                self.hp -= self.bomb_hp
                logger.debug(f"HP lost (bomb hit, {note}), new HP {self.hp}")
            return

        # Score the note
        j = self.get_note_judgement(note)
        self.score += j.score
        self.weighted_hit_notes += j.accuracy_weight

        # Give HP for hit note (heal notes give more)
        if note.type == "heal" and note.hit:
            self.hp += self.heal_hp
        elif note.hit:
            self.hp += j.hp_change
            if j.hp_change < 0:
                logger.debug(f"HP lost (judgement {j} hit, {note}), new HP {self.hp}")

        # Judge the player
        rt = note.hit_time - note.time  # the type checker is stupid, clearly this isn't ever None at this point
        self.latest_judgement = j
        self.latest_judgement_time = self.chart_time
        self.all_judgements.append((self.latest_judgement_time, rt, self.latest_judgement))

        # Animation and hit/miss tracking
        self.last_p1_action = keymap.fourkey.actions[note.lane]
        if note.hit:
            self.hits += 1
            self.streak += 1
            self.last_note_missed = False
        elif note.missed:
            self.misses += 1
            self.max_streak = max(self.streak, self.max_streak)
            self.streak = 0
            self.last_note_missed = True
