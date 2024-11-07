from queue import Queue
from math import ceil
from logging import getLogger
from dataclasses import dataclass
from charm.lib.errors import ThisShouldNeverHappenError

from charm.core.generic.engine import DigitalKeyEvent
from charm.lib.keymap import KeyMap
from charm.lib.types import Seconds, NEVER, FOREVER

from charm.core.generic import Engine, EngineEvent, Judgement
from .chart import ChordShape, FiveFretChart, FiveFretNote, FiveFretChord, FiveFretNoteType, Fret, Ticks

logger = getLogger('charm')

class ChordShapeChangeEvent(EngineEvent):
    def __init__(self, time: Seconds, chord_shape: ChordShape):
        super().__init__(time)
        self.shape = chord_shape


@dataclass
class FiveFretSustainData:
    note: FiveFretNote
    end: Seconds = NEVER
    drop: Seconds = NEVER
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
        print(self.min_fret)
        self.is_tap: bool = self.notes[0].type == FiveFretNoteType.TAP
        self.is_anchored: bool = self.is_single or self.is_tap

        self.is_finished: bool = False

    def get_shape_at_time(self, time: Seconds) -> ChordShape:
        if 7 in self.frets:
            return ChordShape(False, False, False, False, False)
        return ChordShape(*(
                None if (i < self.min_fret and self.is_anchored) else (self.frets.get(i, EMPTY_FRET_DATA).end >= time)
                for i in range(5)
            ))

    def check_finished(self) -> bool:
        for fret_data in self.frets.values():
            if fret_data.drop == NEVER:
                self.is_finished = False
                return False
        self.is_finished = True
        return True

    def drop_sustain(self, time: Seconds, frets: list[int] | None = None) -> None:
        frets = frets or list(self.frets.keys())
        for fret in frets:
            data = self.frets[fret]
            if data.dropped or data.drop != NEVER:
                continue
            data.drop = time
            data.dropped = True
        self.check_finished()

    def finish_sustain(self, time: Seconds, frets: list[int] | None = None) -> None:
        frets = frets or list(self.frets.keys())
        for fret in frets:
            data = self.frets[fret]
            if data.dropped or data.drop != NEVER:
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
        self.last_chord_shape: ChordShape = EMPTY_CHORD
        self.last_strum_time: Seconds = -float('inf')
        self.last_fret_time: Seconds = -float('inf')
        self.tap_shape: ChordShape = EMPTY_CHORD # need to track if we have 'consumed' a chord
        self.active_sustains: list[FiveFretSustain] = []

        self.infinite_front_end = False
        self.linked_disjoints = False # Whether sustains are dropped seperately or together
        self.can_chord_skip = True
        self.punish_chord_skip = True
        self.reward_sustain_accuracy = False # Should sustains reward accurate players?
        # ? self.hopo_leniency: Seconds = 0.080 ? I think this is so you can hit a hopo before you strum as a consession
        self.strum_leniency: Seconds = 0.060 # How much time after a strum occurs that you can fret a note
        self.no_note_leniency: Seconds = 0.030 # If the hit window is empty but there is a note coming within this time, don't overstrum
        self.sustain_end_leniency: Seconds = 0.01 # How early you can release a sustain and still get full points # TODO: impliment

        self.keystate = (False,)*5
        # todo: ignore overstrum during countdown events

        # TODO: move into FiveFretChord somehow.
        # We need a way to get an objective score after the gameplay is over so we need to record the sustain scores.
        self.sustain_scores: list = []

    @property
    def multiplier(self) -> int:
        return min(self.streak // 10 + 1, 4)

    def on_button_press(self, keymap: KeyMap) -> None:
        # ignore spam during front/back porch
        t = self.chart_time
        # hit_win = self.hit_window
        # if t + hit_win < self.chart.notes[0].time or t - hit_win > self.chart.notes[-1].time:
        #     return

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
        # ignore spam during front/back porch
        t = self.chart_time
        # hit_win = self.hit_window
        # if t + hit_win < self.chart.notes[0].time or t - hit_win > self.chart.notes[-1].time:
        #     return

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
        # There is a curious conundrum to solve
        # If we work off of the chords then inputs only get
        # processed when there are chords available,
        # however when using inputs we need to 'catch-up'
        # in the same way for chords

        # TODO: Star Power
        # TODO: Solo

        # ! Not only do we need to handle missed notes, but what about taps with front end?
        self.update_sustains()
        # TODO: self.catch_strum()

        # Remove all missed chords
        # ! What happens if it was a tap/hopo we could have hit using the last chord?
        # ! Or can we safely assert that would have been caught? I think yes, but lets see.
        while self.current_notes and self.current_notes[0].time < self.window_back_end:
            self._miss_chord(self.current_notes.pop(0), float('inf'))

        if not self.current_notes:
            return

        can_tap_hopo = (self.current_notes[0].type == FiveFretNoteType.HOPO and (self.streak > 0 or len(self.current_notes) == len(self.chart.chords)))
        if self.infinite_front_end and self.current_notes[0].time <= self.window_front_end and self.tap_shape.is_open and (can_tap_hopo or self.current_notes[0].type == FiveFretNoteType.TAP):
            self.hit_chord(self.current_notes[0], self.chart_time)
            self.tap_shape = self.last_chord_shape

        # Process all the note inputs
        while self.input_events.qsize() > 0:
            event = self.input_events.get_nowait()

            match event.key:
                case Fret.GREEN:
                    self.on_fret_change(Fret.GREEN, event.new_state=='down', event.time)
                case Fret.RED:
                    self.on_fret_change(Fret.RED, event.new_state=='down', event.time)
                case Fret.YELLOW:
                    self.on_fret_change(Fret.YELLOW, event.new_state=='down', event.time)
                case Fret.BLUE:
                    self.on_fret_change(Fret.BLUE, event.new_state=='down', event.time)
                case Fret.ORANGE:
                    self.on_fret_change(Fret.ORANGE, event.new_state=='down', event.time)
                case "strum":
                    self.on_strum(event.time)
                case _:
                    raise ThisShouldNeverHappenError

    def on_fret_change(self, fret: Fret, pressed: bool, time: Seconds) -> None:
        # First we check against sustains
        # Then we can do the strum
        # Then we do Taps and Hopos
        # Also update the last chord shape

        # Sustains have some oddities because they 'ghost' the user's input.
        # A chord matches even if the player is holding down extra notes IF they are for sustains.

        # TODO:
        # Sustains
        # Ghosting

        current_chord = self.current_notes[0]
        last_shape = self.last_chord_shape
        last_strum = self.last_strum_time

        # Because we have already cleared away all out of data chords we only need to check the front end
        has_active_chord = current_chord.time <= self.window_front_end

        self.last_chord_shape = chord_shape = last_shape.update_fret(fret, pressed)
        self.last_fret_time = time

        self.keystate = tuple(chord_shape)  # type: ignore -- :p

        # update the tap shape since the chord is no longer 'consumed'
        if not chord_shape.matches(self.tap_shape):
            self.tap_shape = EMPTY_CHORD

        for sustain in self.active_sustains:
            # There is no case where an open sustain could be a disjoint so we only care about this sole case
            if 7 in sustain.frets and not chord_shape.is_open and not has_active_chord:
                sustain.drop_sustain(time)
                continue
            
            shape = sustain.get_shape_at_time(time)
            print( self.linked_disjoints, not sustain.is_disjoint, (has_active_chord and chord_shape.contains(shape)), chord_shape.matches(shape))
            if self.linked_disjoints or not sustain.is_disjoint and ((has_active_chord and chord_shape.contains(shape)) or chord_shape.matches(shape)):
                print('wow!')
                sustain.drop_sustain(time)
                self.score_sustain(sustain)
                continue

            sustain_finished = True
            for idx, fretting in enumerate(shape):
                # anchoring is an easy check
                if fretting is None:
                    continue

                chord_fretting = chord_shape[idx]
                
                # While the sustain isn't being extended we aren't lenient about chord over-pressing.
                # This is the 'match' check from above... kinda
                if not has_active_chord and not fretting and chord_fretting:
                    sustain.drop_sustain(time)
                    sustain_finished = True
                    break

                if not fretting: # equivalent to checking if idx in sustain.frets
                    continue

                data = sustain.frets[idx]
                if data.dropped or data.drop != NEVER:
                    continue
                
                # This is the 'contain' check from above... kinda
                if not chord_fretting:
                    data.drop = time
                    data.dropped = True
                    continue

                sustain_finished = False

            sustain.is_finished = sustain_finished
            if sustain_finished:
                self.score_sustain(sustain)
                self.active_sustains.remove(sustain)

        if not has_active_chord:
            # The current chord isn't available to process,
            # but we needed to update the chord shape, and handle sustain fretting.
            return

        # While this could be done in the previous sustain loop this is easier logically
        # We use the anchoring logic to easily ignore ghosted inputs
        ghost_shape = chord_shape
        for sustain in self.active_sustains:
            for fret, data in sustain.frets.items():
                if not data.dropped or data.drop != NEVER:
                    ghost_shape = ghost_shape.update_fret(fret, None)


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
                return


    def on_strum(self, time: Seconds) -> None:
        # First we check for overstrum
        # Then we check for struming notes
        # If we didn't hit a chord then lets look into the future
        # If that didn't work then 'start' the strum leniency

        # TODO:
        # No Input Ghosting
        # No Chord Skipping
        # Prolly so much else lmao

        current_chord = self.current_notes[0]
        current_shape = self.last_chord_shape
        last_strum = self.last_strum_time

        # TODO: Change this to record when the overstrum will occur
        # TODO: This means we can easily track multiple levels of leniency
        if abs(time - last_strum) <= self.strum_leniency:
            self.overstrum()
        self.last_strum_time = time

        if not (self.window_back_end <= current_chord.time <= self.window_front_end):
            # The current chord isn't available to process,
            # but we needed to process overstrum
            self.drop_sustains(time)
            return
 
        if current_shape.matches(current_chord.shape):
            self.hit_chord(current_chord, time)
            self.last_strum_time = -float('inf')
            return

        if self.can_chord_skip:
            pass

        # If fail to chord skip then break sustains
        self.drop_sustains(time)

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

        if chord.length > 0.0:
            self.begin_sustain(chord, time)

    def score_chord(self, chord: FiveFretChord) -> None:
        if chord.hit:
            self.score += 50 * self.multiplier * chord.size

    def update_sustains(self):
        time = self.chart_time + self.sustain_end_leniency
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

    def score_sustain(self, sustain: FiveFretSustain) -> bool:
        print('sajkdhaskhj')
        rolling_score = 0
        start = sustain.start
        for fret_data in sustain.frets.values():
            if fret_data.drop == NEVER:
                break
            ticks_held = fret_data.note.tick_length * (fret_data.drop - start) / (fret_data.end - start)
            raw_score = ticks_held * 25 / self.chart.resolution
            rolling_score += raw_score
        else:
            # We only want to score the sustain when every fret has been dropped/finished.
            self.sustain_scores.append(FiveFretSustainScore(start, sustain.hit_time, sustain.frets, sustain.chord, rolling_score, self.multiplier))
            self.score += ceil(rolling_score) * sustain.multiplier
            return True
        return False

    def overstrum(self) -> None:
        logger.info(f'Overstrummed at t={self.chart_time}')

    # def generate_results(self) -> Results[C]:
    #     raise NotImplementedError
