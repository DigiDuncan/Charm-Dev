from queue import Queue
from logging import getLogger
from charm.lib.errors import ThisShouldNeverHappenError

from charm.core.generic.engine import DigitalKeyEvent
from charm.lib.keymap import KeyMap
from charm.lib.types import Seconds

from charm.core.generic import Engine, EngineEvent, Judgement
from .chart import ChordShape, FiveFretChart, FiveFretNote, FiveFretChord, FiveFretNoteType, Fret

logger = getLogger('charm')

class ChordShapeChangeEvent(EngineEvent):
    def __init__(self, time: Seconds, chord_shape: ChordShape):
        super().__init__(time)
        self.shape = chord_shape

class FiveFretSustain:

    def __init__(self, chord: FiveFretChord, start: Seconds) -> None:
        self._chord: FiveFretChord = chord
        self._start: Seconds = start

        self._broken: bool = False
        self._break_time: Seconds = -float('inf')

        self._is_disjointed: bool = not (len(self._chord.frets) != 1 and all(
            self._chord.notes[0].length == note.length for note in self._chord.notes
        ))

        self._times: dict[int, Seconds] = {
            note.lane: note.end for note in self._chord.notes
        }
        self._min_fret: int = min(self._times.keys())
        self._is_tap: bool = self._chord.notes[0].type == FiveFretNoteType.TAP
        self._end = max(self._times.values())

    @property
    def end(self) -> Seconds:
        return self._end

    def get_shape(self, time: Seconds) -> ChordShape:
        if self._is_disjointed:
            return ChordShape(*(
                None if (i < self._min_fret and self._is_tap) else (self._times.get(i, float('inf')) <= time)
                for i in range(5)
            ))
        if 7 in self._chord.frets:
            # Open note
            return ChordShape(False, False, False, False, False)
        if len(self._chord.frets) == 1:
            # Single notes
            lanes = self._chord.notes[0].lane
            return ChordShape(
                None if 0 < lanes else 0 == lanes,  # Green
                None if 1 < lanes else 1 == lanes,  # Red
                None if 2 < lanes else 2 == lanes,  # Yellow
                None if 3 < lanes else 3 == lanes,  # Blue
                None if 4 < lanes else 4 == lanes,  # Orange
            )
        else:
            # Chords
            return ChordShape(
                *(
                    None if (i < self._min_fret and self._is_tap) else i in self._times
                    for i in range(5)
                )
            )

    def break_sustain(self, time: float):
        self._broken = True
        self._break_time = time


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
        self.can_chord_skip = True
        self.punish_chord_skip = True
        # ? self.hopo_leniency: Seconds = 0.080 ? I think this is so you can hit a hopo before you strum as a consession
        self.strum_leniency: Seconds = 0.060 # How much time after a strum occurs that you can fret a note
        self.no_note_leniency: Seconds = 0.030 # If the hit window is empty but there is a note coming within this time, don't overstrum
        self.sustain_end_leniency: Seconds = 0.01 # How early you can release a sustain and still get full points

        self.keystate = (False,)*5
        # todo: ignore overstrum during countdown events

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
        elif keymap.hero.strumup.released:
            # kept sep incase we want to track
            self.input_events.put_nowait(DigitalKeyEvent(t, "strum", "up"))
        elif keymap.hero.strumdown.released:
            self.input_events.put_nowait(DigitalKeyEvent(t, "strum", "up"))

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


    def update_sustains(self):
        for sustain in self.active_sustains[:]:
            if sustain.end - self.sustain_end_leniency < self.chart_time:
                logger.info('Sustain finished')
                self.active_sustains.remove(sustain)

    def break_sustains(self, time: float):
        logger.info('broken all sustains')
        for sustain in self.active_sustains:
            sustain.break_sustain(time)

    def on_fret_change(self, fret: Fret, pressed: bool, time: Seconds) -> None:
        # First we check against sustains
        # Then we do Taps and Hopos
        # Then we can do the strum
        # Also update the last chord shape

        # TODO:
        # Sustains
        # Taps and Hopos
        #  Anchoring and Ghosting

        current_chord = self.current_notes[0]
        last_shape = self.last_chord_shape
        last_strum = self.last_strum_time

        self.last_chord_shape = chord_shape = last_shape.update_fret(fret, pressed)
        self.last_fret_time = time

        self.keystate = tuple(chord_shape)  # type: ignore -- :p

        # update the tap shape since the chord is no longer 'consumed'
        if not chord_shape.matches(self.tap_shape):
            self.tap_shape = EMPTY_CHORD

        if not (self.window_back_end <= current_chord.time <= self.window_front_end):
            # The current chord isn't available to process,
            # but we needed to update the chord shape
            return

        if chord_shape.matches(current_chord.shape):
            if abs(time - last_strum) <= self.strum_leniency:
                # * Because we can strum any note irrespective of its type
                # * this works for Taps and Hopos
                self.hit_chord(current_chord, time)
                self.last_strum_time = -float('inf')
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
            self.break_sustains(time)
            return

        if current_shape.matches(current_chord.shape):
            self.hit_chord(current_chord, time)
            self.last_strum_time = -float('inf')
            return

        if self.can_chord_skip:
            pass

        # If fail to chord skip then break sustains
        self.break_sustains(time)

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
            self.active_sustains.append(FiveFretSustain(chord, time))

    def start_sustain(self, chord: FiveFretChord, time: float) -> None:
        pass

    def score_chord(self, chord: FiveFretChord) -> None:
        if chord.hit:
            self.score += 50 * min(self.streak // 10 + 1, 4)

    def score_sustain(self, note: FiveFretNote) -> None:
        raise NotImplementedError

    def overstrum(self) -> None:
        logger.info(f'Overstrummed at t={self.chart_time}')

    # def generate_results(self) -> Results[C]:
    #     raise NotImplementedError
