from queue import Queue
from math import ceil
from logging import getLogger
from dataclasses import dataclass
from charm.game.generic.results import Results
from charm.lib.errors import ThisShouldNeverHappenError

from charm.game.generic.engine import DigitalKeyEvent
from charm.core.keymap import KeyMap
from charm.lib.types import Seconds, NEVER, FOREVER

from charm.game.generic import Engine, EngineEvent, Judgement
from .chart import ChordShape, FiveFretChart, FiveFretNote, FiveFretChord, FiveFretNoteType, Fret, Ticks, StarpowerEvent, SoloEvent

logger = getLogger('charm')

class ChordShapeChangeEvent(EngineEvent):
    def __init__(self, time: Seconds, chord_shape: ChordShape):
        super().__init__(time)
        self.shape = chord_shape


@dataclass
class FiveFretSustainData:
    note: FiveFretNote
    end: Seconds = NEVER
    drop: Seconds = FOREVER
    dropped: bool = False

EMPTY_FRET_DATA = FiveFretSustainData(None)  # type: ignore

class FiveFretSustain:
    def __init__(self, chord: FiveFretChord, notes: list[FiveFretNote], time: Seconds, multiplier: int) -> None:
        self.chord: FiveFretChord = chord
        self.notes: list[FiveFretNote] = notes
        self.start: Seconds = notes[0].time
        self.end: Seconds = max(note.end for note in notes)
        self.hit_time: Seconds = time # TODO: let this influence how the sustain is scored
        self.multiplier: int = multiplier

        self.frets: dict[int, FiveFretSustainData] = {
            note.lane: FiveFretSustainData(note, note.end) for note in notes
        }

        self.is_single: bool = len(self.notes) == 1
        self.is_disjoint: bool = not(
            not self.is_single
            and
            all(self.notes[0].length == note.length for note in self.notes)
        )
        self.min_fret: int = min(self.frets.keys())
        self.is_open: bool = 7 in self.frets and self.chord.size == 1
        self.is_tap: bool = self.notes[0].type == FiveFretNoteType.TAP
        self.is_anchored: bool = self.is_single or (self.is_tap and not self.is_open)

        self.is_finished: bool = False

    def get_shape_at_time(self, time: Seconds) -> ChordShape:
        if self.is_open:
            return ChordShape(False, False, False, False, False)
        return ChordShape(*(
                None if (i < self.min_fret and self.is_anchored) else (self.frets.get(i, EMPTY_FRET_DATA).end >= time)
                for i in range(5)
            ))

    def check_finished(self) -> bool:
        for fret_data in self.frets.values():
            if fret_data.drop == FOREVER:
                break
        else:
            self.is_finished = True
            return True
        self.is_finished = False
        return False

    def drop_sustain(self, time: Seconds, frets: list[int] | None = None) -> None:
        frets = frets or list(self.frets.keys())
        for fret in frets:
            data = self.frets[fret]
            if data.dropped or data.drop != FOREVER:
                continue
            data.drop = time
            data.dropped = True
        self.check_finished()

    def finish_sustain(self, time: Seconds, frets: list[int] | None = None) -> None:
        frets = frets or list(self.frets.keys())
        for fret in frets:
            data = self.frets[fret]
            if data.dropped or data.drop != FOREVER:
                continue
            data.drop = time
        self.check_finished()


# TODO: update to work with seperate frets in sustain
@dataclass
class FiveFretSustainScore:
    start_time: Seconds
    hit_time: float # unused atm

    frets: dict[int, FiveFretSustainData]
    chord: FiveFretChord

    raw_score: float
    multiplier: int

EMPTY_CHORD = ChordShape(False, False, False, False, False)


class FiveFretEngine(Engine[FiveFretChart, FiveFretNote]):
    def __init__(self, chart: FiveFretChart, offset: Seconds = 0):
        judgements = [
            Judgement('Pass', 'pass', 140, 10, 1),
            Judgement('Miss', 'miss', float('inf'), 0, 0),
        ]
        super().__init__(chart, judgements, offset)
        self.current_notes: list[FiveFretChord] = self.chart.chords[:] # Override the default engine

        self.input_events: Queue[DigitalKeyEvent] = Queue()

        # There are rolling values from the update, which sucks,
        # but we also need to store it between frames so its okay?
        self.processed_time: Seconds = 0.0
        self.last_chord_shape: ChordShape = EMPTY_CHORD
        self.last_strum_time: Seconds = NEVER
        self.last_fret_time: Seconds = NEVER
        self.last_hopo_tap_time: Seconds = NEVER
        self.tap_shape: ChordShape = EMPTY_CHORD # need to track if we have 'consumed' a chord
        self.active_sustains: list[FiveFretSustain] = []

        self.infinite_front_end = False
        self.linked_disjoints = True # Whether sustains are dropped seperately or together
        self.can_chord_skip = True
        self.punish_chord_skip = True
        self.extended_starpower = True # TODO
        self.reward_sustain_accuracy = False # Should sustains reward accurate players?
        self.hopo_leniency: Seconds = 0.080 # lenience so you can't overstrum a tapped hopo
        self.strum_leniency: Seconds = 0.060 # How much time after a strum occurs that you can fret a note
        self.no_note_leniency: Seconds = 0.030 # If the hit window is empty but there is a note coming within this time, don't overstrum
        self.sustain_end_leniency: Seconds = 0.01 # How early you can release a sustain and still get full points

        self.keystate = (False,)*5
        # todo: ignore overstrum during countdown events

        # TODO: move into FiveFretChord somehow.
        # We need a way to get an objective score after the gameplay is over so we need to record the sustain scores.
        self.sustain_scores: list = []

        # The actual score
        self.commited_score: int = 0

        # I guess we need this for Results
        self.latest_judgement = None
        self.latest_judgement_time = None
        self.all_judgements: list[tuple[Seconds, Seconds, Judgement]] = []

        self.star_power: float = 0.0
        self.star_power_active: bool = False
        self.star_power_time: float = FOREVER
        self.star_power_phrase: bool = False
        self.star_power_broken: bool = False
        self.star_power_event: StarpowerEvent | None = None if not self.chart.indices.star_time.items else self.chart.indices.star_time.items[0]
        self.next_star_power_idx: int = 1

        self.solo_active: bool = False
        self.solo_time: float = FOREVER
        self.solo_note_count: int = 0
        self.solo_hit_count: int = 0
        self.solo_event: SoloEvent | None = None if not self.chart.indices.solo_time.items else self.chart.indices.solo_time.items[0]
        self.next_solo_idx: int = 1

        # TODO: Update parser to make chords with star power and solo.

    @property
    def multiplier(self) -> int:
        return min(self.streak // 10 + 1, 4)

    def on_button_press(self, keymap: KeyMap) -> None:
        t = self.chart_time

        # Get the current hero action being pressed
        if keymap.hero.green.pressed:
            self.input_events.put_nowait(DigitalKeyEvent(t, Fret.GREEN, "down"))
        elif keymap.hero.red.pressed:
            self.input_events.put_nowait(DigitalKeyEvent(t, Fret.RED, "down"))
        elif keymap.hero.yellow.pressed:
            self.input_events.put_nowait(DigitalKeyEvent(t, Fret.YELLOW, "down"))
        elif keymap.hero.blue.pressed:
            self.input_events.put_nowait(DigitalKeyEvent(t, Fret.BLUE, "down"))
        elif keymap.hero.orange.pressed:
            self.input_events.put_nowait(DigitalKeyEvent(t, Fret.ORANGE, "down"))
        elif keymap.hero.strumup.pressed:
            # kept sep incase we want to track
            self.input_events.put_nowait(DigitalKeyEvent(t, "strum", "down"))
        elif keymap.hero.strumdown.pressed:
            self.input_events.put_nowait(DigitalKeyEvent(t, "strum", "down"))

    def on_button_release(self, keymap: KeyMap) -> None:
        t = self.chart_time
        # Get the current hero action being released
        if keymap.hero.green.released:
            self.input_events.put_nowait(DigitalKeyEvent(t, Fret.GREEN, "up"))
        elif keymap.hero.red.released:
            self.input_events.put_nowait(DigitalKeyEvent(t, Fret.RED, "up"))
        elif keymap.hero.yellow.released:
            self.input_events.put_nowait(DigitalKeyEvent(t, Fret.YELLOW, "up"))
        elif keymap.hero.blue.released:
            self.input_events.put_nowait(DigitalKeyEvent(t, Fret.BLUE, "up"))
        elif keymap.hero.orange.released:
            self.input_events.put_nowait(DigitalKeyEvent(t, Fret.ORANGE, "up"))

    def pause(self) -> None:
        pass

    def unpause(self) -> None:
        pass

    def calculate_score(self) -> None:
        # Because the chart time will always be later than the input times we run though all the inputs since the
        # last update first. Then if the processed time is behind the chart time we do one last pass to bring everything up to speed.
        # This is what Yarg is doing, but their functions are so strangely formatted that it was hard to understand.

        self.process_inputs()
        self.calculate_uncommited()

        # The inputs have caught everything up to where the chart actually is so we can wash our hands of everything
        if self.chart_time <= self.processed_time:
            return
        
        self.process_to_time(self.chart_time)

    def process_inputs(self):
        # Process all the note inputs
        while self.input_events.qsize() > 0:
            event = self.input_events.get_nowait()
            time = event.time
    
            self.process_to_time(time)

            # Ignore inputs when no notes or sustsains are left
            if not self.current_notes and not self.active_sustains:
                continue
    
            match event.key:
                case Fret.GREEN:
                    self.on_fret_change(Fret.GREEN, event.new_state=='down', time)
                case Fret.RED:
                    self.on_fret_change(Fret.RED, event.new_state=='down', time)
                case Fret.YELLOW:
                    self.on_fret_change(Fret.YELLOW, event.new_state=='down', time)
                case Fret.BLUE:
                    self.on_fret_change(Fret.BLUE, event.new_state=='down', time)
                case Fret.ORANGE:
                    self.on_fret_change(Fret.ORANGE, event.new_state=='down', time)
                case "strum":
                    self.on_strum(time)
                case _:
                    raise ThisShouldNeverHappenError
                
    def process_to_time(self, time: Seconds):
        self.update_sustains(time)

        if self.current_notes:
            # The first thing that needs to be checked is the front end as this occurs irrespective of the notes
            self.process_infinite_frontend(time)

            # Run through every note making sure to not miss the start / end of a solo.
            while self.current_notes and self.current_notes[0].time + self.hit_window < time:
                note = self.current_notes.pop(0)
                self.process_starpower(note.time)
                self.process_solo(note.time)
                self._miss_chord(note, FOREVER)

        # We need to bring these up to this point in time
        self.process_starpower(time)
        self.process_solo(time)

        self.processed_time = time
                
    def calculate_uncommited(self) -> None:
        base = self.commited_score
        rolling = sum(ceil(self.get_sustain_score(sustain)) * sustain.multiplier for sustain in self.active_sustains)

        self.score = base + rolling

    def process_infinite_frontend(self, time: Seconds):
        # Do all the easy early-exit checks
        if not self.infinite_front_end or time < self.current_notes[0].time - self.hit_window or not self.tap_shape.is_open:
            return
        
        # If the first unprocessed note wasn't a tap or tap-able hopo then we are done here
        can_tap_hopo = (self.current_notes[0].type == FiveFretNoteType.HOPO and (self.streak > 0 or len(self.current_notes) == len(self.chart.chords)))
        if not (can_tap_hopo or self.current_notes[0].type != FiveFretNoteType.TAP):
            return

        ghost_shape = self.calculate_ghost_shape(self.last_chord_shape)
        if not ghost_shape.matches(self.current_notes[0].shape):
            return
        
        self.hit_chord(self.current_notes[0], time)
        self.tap_shape = self.last_chord_shape
        if can_tap_hopo:
            self.last_hopo_tap_time = time
        
    def process_starpower(self, time: Seconds):
        if self.star_power_event is None or time < self.star_power_event.time:
            # If there is no star power event then the starpower has finished for the song
            return
        
        if self.star_power_active:
            if not self.star_power_broken:
                self.star_power += 0.25
            self.star_power_active = False
            self.star_power_time = FOREVER
        else:
            self.star_power_active = True
            self.star_power_time = self.star_power_event.time
        
        self.star_power_broken = False

        # The star power event has passed so we need to get the next star power event.
        if len(self.chart.indices.star_time.items) <= self.next_star_power_idx:
            self.star_power_event = None
            return

        self.star_power_event = self.chart.indices.star_time.items[self.next_star_power_idx]
        self.next_star_power_idx += 1
        
    def process_solo(self, time: Seconds):
        if self.solo_event is None or time < self.solo_event.time:
            # If there is no solo event then the solos are finished for the song
            return

        if self.solo_active:
            # The solo has finished so score the solo.
            if self.solo_note_count != 0:
                fraction = self.solo_hit_count / self.solo_note_count
                logger.info(f'Solo hit with {fraction*100:.0f}% accuracy')
            self.solo_active = False
            self.solo_time = FOREVER
        else:
            self.solo_active = True
            self.solo_time = self.solo_event.time

        
        self.solo_hit_count = 0
        self.solo_note_count = 0

        if len(self.chart.indices.solo_time.items) <= self.next_solo_idx:
            self.solo_event = None
            return
        
        self.solo_event = self.chart.indices.solo_time.items[self.next_solo_idx]
        self.next_solo_idx += 1

    def on_fret_change(self, fret: Fret, pressed: bool, time: Seconds) -> None:
        # First we check against sustains
        # Then we can do the strum
        # Then we do Taps and Hopos
        # Also update the last chord shape

        # Sustains have some oddities because they 'ghost' the user's input.
        # A chord matches even if the player is holding down extra notes IF they are for sustains.

        if not self.current_notes:
            current_chord = None
            has_active_chord = False
        else:
            current_chord = self.current_notes[0]
            # Because we have already cleared away all out of data chords we only need to check the front end
            has_active_chord = current_chord.time <= time + self.hit_window

        last_shape = self.last_chord_shape
        last_strum = self.last_strum_time

        self.last_chord_shape = chord_shape = last_shape.update_fret(fret, pressed)
        self.last_fret_time = time

        self.keystate = tuple(chord_shape)  # type: ignore -- :p

        # update the tap shape since the chord is no longer 'consumed'
        if not chord_shape.matches(self.tap_shape):
            self.tap_shape = EMPTY_CHORD

        # When we do sustains we have to check for 'lift-off' because the player may be
        # moving towards the correct sustain fretting, and we have to be lenient on them
        # TODO: add a lenience timer for this? Say they have 1/30th of a second to lift off before its marked as wrong?

        for sustain in self.active_sustains:
            shape = sustain.get_shape_at_time(time)
            # We are lenient on lift-off
            # TODO: We need to account for ghosted notes for open sustains :melt:
            if shape.is_open and (not chord_shape.is_open and pressed) and not has_active_chord:
                logger.info('open sustain dropped')
                sustain.drop_sustain(time)
                self.score_sustain(sustain)
                self.active_sustains.remove(sustain)
                continue
            
            if (self.linked_disjoints or not sustain.is_disjoint) and not ((has_active_chord and chord_shape.contains(shape)) or chord_shape.matches(shape)):
                logger.info('linked sustain dropped')
                sustain.drop_sustain(time)
                self.score_sustain(sustain)
                self.active_sustains.remove(sustain)
                continue
            
            # TODO: handle disjointed open chords :melt:
            sustain_finished = True
            for idx, fretting in enumerate(shape):
                # anchoring is an easy check
                if fretting is None:
                    continue

                chord_fretting = chord_shape[idx]
                
                # While the sustain isn't being extended we aren't lenient about chord over-pressing.
                # This is the 'match' check from above... kinda
                if not has_active_chord and not fretting and chord_fretting:
                    logger.info('sustain over-pressed')
                    sustain.drop_sustain(time)
                    sustain_finished = True
                    break

                if not fretting: # equivalent to checking if idx in sustain.frets
                    continue

                data = sustain.frets[idx]
                if data.dropped or data.drop != FOREVER:
                    continue

                # This is the 'contain' check from above... kinda
                if not chord_fretting:
                    data.drop = time
                    data.dropped = True
                    continue

                sustain_finished = False

            # TODO: This doesn't account for open chords
            sustain.is_finished = sustain_finished
            if sustain_finished:
                logger.info('sustain dropped and finished')
                self.score_sustain(sustain)
                self.active_sustains.remove(sustain)

        if not has_active_chord or current_chord is None:
            # The current chord isn't available to process,
            # but we needed to update the chord shape, and handle sustain fretting.
            return

        # While this could be done in the previous sustain loop this is easier logically
        # We use the anchoring logic to easily ignore ghosted inputs
        ghost_shape = self.calculate_ghost_shape(chord_shape)

        if ghost_shape.matches(current_chord.shape):
            if abs(time - last_strum) <= self.strum_leniency:
                # * Because we can strum any note irrespective of its type
                # * this works for Taps and Hopos
                self.hit_chord(current_chord, time)
                self.last_strum_time = NEVER
                return

            can_tap_hopo = (current_chord.type == FiveFretNoteType.HOPO and (self.streak > 0 or len(self.current_notes) == len(self.chart.chords)))
            if (can_tap_hopo or current_chord.type == FiveFretNoteType.TAP) and self.tap_shape.is_open:
                self.hit_chord(current_chord, time)
                self.tap_shape = chord_shape

                if can_tap_hopo:
                    self.last_hopo_tap_time = time
    
    def calculate_ghost_shape(self, shape: ChordShape):
        ghost_shape = shape
        for sustain in self.active_sustains:
            for fret, data in sustain.frets.items():
                if fret == 7:
                    continue
                if not data.dropped or data.drop != FOREVER:
                    ghost_shape = ghost_shape.update_fret(fret, None)
        return ghost_shape

    def on_strum(self, time: Seconds) -> None:
        # First we check for overstrum
        # Then we check for struming notes
        # If we didn't hit a chord then lets look into the future
        # If that didn't work then 'start' the strum leniency

        # Overstrum if there are no notes, but there are active sustains
        if not self.current_notes and self.active_sustains:
            self.overstrum(time)
            return

        current_chord = self.current_notes[0]
        chord_shape = self.last_chord_shape
        last_strum = self.last_strum_time

        # TODO: Change this to record when the overstrum will occur
        # TODO: This means we can easily track multiple levels of leniency
        if abs(time - last_strum) <= self.strum_leniency:
            self.overstrum(time)
        self.last_strum_time = time

        # Because we have already cleared away all out of data chords we only need to check the front end
        has_active_chord = current_chord.time <= time + self.hit_window

        if not has_active_chord:
            # The current chord isn't available to process,
            # but we needed to process overstrum
            self.overstrum(time)
            self.last_strum_time = -float('inf')
            return

        # We use the anchoring logic to easily ignore ghosted inputs
        ghost_shape = self.calculate_ghost_shape(chord_shape)
 
        if ghost_shape.matches(current_chord.shape):
            self.hit_chord(current_chord, time)
            self.last_strum_time = -float('inf')
            return

        if self.can_chord_skip:
            for idx, chord in enumerate(self.current_notes[1:]):
                if self.window_front_end < chord.time:
                    # We have reached the end of the chords in the hit window
                    break
                if ghost_shape.matches(chord.shape):
                    if self.punish_chord_skip:
                        for missed in self.current_notes[:idx]:
                            self.miss_chord(missed, time)
                    self.hit_chord(chord, time)
                    return

        # If fail to chord skip then break sustains
        self.overstrum(time)

    def miss_chord(self, chord: FiveFretChord, time: float = float('inf')) -> None:
        if chord.missed or chord.hit:
            return
        self._miss_chord(chord, time)
        self.current_notes.remove(chord)

    def _miss_chord(self, chord: FiveFretChord, time: float) -> None:
        chord.missed = True
        chord.hit_time = time
        self.score_chord(chord)

        self.max_streak = max(self.max_streak, self.streak)
        self.streak = 0

        if self.star_power_active and self.star_power_time < chord.time:
            self.star_power_broken = True

        if self.solo_active and self.solo_time < chord.time:
            self.solo_note_count += 1

    def hit_chord(self, chord: FiveFretChord, time: float) -> None:
        if chord.missed or chord.hit:
            return
        self._hit_chord(chord, time)
        self.current_notes.remove(chord)

    def _hit_chord(self, chord: FiveFretChord, time: float) -> None:
        chord.hit = True
        chord.hit_time = time
        self.score_chord(chord)

        self.streak += 1
        self.max_streak = max(self.max_streak, self.streak)

        if self.solo_active and self.solo_time < chord.time:
            self.solo_note_count += 1
            self.solo_hit_count += 1

        if chord.length > 0.0:
            self.begin_sustain(chord, time)

    def score_chord(self, chord: FiveFretChord) -> None:
        if chord.hit:
            self.commited_score += 50 * self.multiplier * chord.size
            self.weighted_hit_notes += 1
            self.hits += 1
        elif chord.missed:
            self.misses += 1

        # Judge the player ... kinda?
        rt = chord.hit_time - chord.time  # type: ignore -- the type checker is stupid, clearly this isn't ever None at this point
        j = self.get_note_judgement(chord) # type: ignore -- look into this.
        self.latest_judgement = j
        self.latest_judgement_time = self.chart_time
        self.all_judgements.append((self.latest_judgement_time, rt, self.latest_judgement))

    def update_sustains(self, time: Seconds):
        time = time + self.sustain_end_leniency
        for sustain in self.active_sustains[:]:
            sustain_finished = True
            for data in sustain.frets.values():
                if data.end <= time:
                    data.drop = data.end
                else:
                    sustain_finished = False
            sustain.is_finished = sustain_finished
            if sustain_finished:
                self.score_sustain(sustain)
                self.active_sustains.remove(sustain)

    def drop_sustains(self, time: Seconds):
        for sustain in self.active_sustains:
            sustain.drop_sustain(time)
            self.score_sustain(sustain)
        self.active_sustains = []

    def begin_sustain(self, chord: FiveFretChord, time: Seconds):
        self.active_sustains.append(FiveFretSustain(chord, chord.notes, time, self.multiplier))

    def get_sustain_score(self, sustain: FiveFretSustain) -> float:
        rolling = 0.0
        start = sustain.start
        for fret_data in sustain.frets.values():
            drop = min(fret_data.drop, self.chart_time)
            ticks_held = fret_data.note.tick_length * (drop - start) / (fret_data.end - start)
            raw = ticks_held * 25 / self.chart.resolution
            rolling += raw

        return rolling


    def score_sustain(self, sustain: FiveFretSustain) -> bool:
        if not sustain.is_finished:
            return False

        score = self.get_sustain_score(sustain)

        # We only want to score the sustain when every fret has been dropped/finished.
        self.sustain_scores.append(FiveFretSustainScore(sustain.start, sustain.hit_time, sustain.frets, sustain.chord, score, sustain.multiplier))
        self.commited_score += ceil(score) * sustain.multiplier
        return True

    def overstrum(self, time: Seconds) -> None:
        # If you just tapped a hopo we need to be nicer about over strumming
        if self.last_hopo_tap_time + self.hopo_leniency < time:
            self.last_hopo_tap_time = NEVER
            return

        logger.info('overstrummed')
        self.drop_sustains(time)

        # Star Power and Solo

        self.max_streak = max(self.streak, self.max_streak)
        self.streak = 0

    def generate_results(self) -> Results:
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
