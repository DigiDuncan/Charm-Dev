from queue import Queue
from charm.lib.errors import ThisShouldNeverHappenError

from charm.core.generic.engine import DigitalKeyEvent
from charm.lib.keymap import keymap
from charm.lib.types import Seconds

from charm.core.generic import Engine, EngineEvent, Judgement
from .chart import ChordShape, FiveFretChart, FiveFretNote, FiveFretChord, FiveFretNoteType, Fret


class ChordShapeChangeEvent(EngineEvent):
    def __init__(self, time: Seconds, chord_shape: ChordShape):
        super().__init__(time)
        self.shape = chord_shape


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

        self.infinite_front_end = False
        self.can_chord_skip = True
        self.punish_chord_skip = True
        # ? self.hopo_leniency: Seconds = 0.080 ? I think this is so you can hit a hopo before you strum as a consession
        self.strum_leniency: Seconds = 0.060 # How much time after a strum occurs that you can fret a note
        self.no_note_leniency: Seconds = 0.030 # If the hit window is empty but there is a note coming within this time, don't overstrum
        self.sustain_end_leniency: Seconds = 0.01 # How early you can release a sustain and still get full points

        # todo: ignore overstrum during countdown events

    def on_key_press(self, symbol: int, modifiers: int) -> None:
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


    def on_key_release(self, symbol: int, modifiers: int) -> None:
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

        # ! Not only do we need to handle missed notes, but what about taps with front end?
        # TODO: self.update_sustains()
        # TODO: self.catch_strum()

        # Remove all missed chords
        # ! What happens if it was a tap/hopo we could have hit using the last chord?
        # ! Or can we safely assert that would have been caught? I think yes, but lets see.
        while self.current_notes and self.current_notes[0].time < self.window_back_end:
            # print(len(self.current_notes))
            self.miss_chord(self.current_notes[0])

        if not self.current_notes:
            return # ! We are out of notes, but we still need to handle sustains hmmmm.

        # ? Could we maybe just check the first valid tap in here ?
        # ? Also if you miss a note does that invalidate the tap ?

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

        if not (self.window_back_end <= current_chord.time <= self.window_front_end):
            # The current chord isn't available to process,
            # but we needed to update the chord shape
            return

        if abs(time - last_strum) <= self.strum_leniency and chord_shape.matches(current_chord.shape):
            # * Because we can strum any note irrespective of its type
            # * this works for Taps and Hopos
            self.hit_chord(current_chord, time)
            self.last_strum_time = -float('inf')
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
            return

        if not (self.window_back_end <= current_chord.time <= self.window_front_end):
            # The current chord isn't available to process,
            # but we needed to process overstrum
            return

        if current_shape.matches(current_chord.shape):
            self.hit_chord(current_chord, time)
            self.last_strum_time = -float('inf')
            return

        if self.can_chord_skip:
            pass

        self.last_strum_time = time


    def miss_chord(self, chord: FiveFretChord, time: float = float('inf')) -> None:
        print('!MISS!')
        chord.missed = True
        chord.hit_time = time
        self.score_chord(chord)
        self.current_notes.remove(chord)

    def hit_chord(self, chord: FiveFretChord, time: float) -> None:
        print('!CHORD!')
        chord.hit = True
        chord.hit_time = time
        self.score_chord(chord)
        self.current_notes.remove(chord)

        # TODO: Add sustain


    def score_chord(self, chord: FiveFretChord) -> None:
        pass

    def score_tap(self, chord: FiveFretChord) -> None:
        raise NotImplementedError

    def score_sustain(self, note: FiveFretNote) -> None:
        raise NotImplementedError

    def overstrum(self) -> None:
        print('!OVERSTRUM!')

    # def generate_results(self) -> Results[C]:
    #     raise NotImplementedError
