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
        self.hopo_leniency: Seconds = 0.080
        self.strum_leniency: Seconds = 0.060
        self.no_note_leniency: Seconds = 0.030
        self.sustain_end_leniency: Seconds = 0.01

        # todo: ignore overstrum during countdown events

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        # ignore spam during front/back porch
        t = self.chart_time
        hit_win = self.hit_window
        if t + hit_win < self.chart.notes[0].time or t - hit_win > self.chart.notes[-1].time:
            return

        # Get the current hero action being pressed
        current_action = keymap.hero.pressed_action
        if current_action is None:
            return

        if current_action in {keymap.hero.green, keymap.hero.red, keymap.hero.yellow, keymap.hero.blue, keymap.hero.orange}:
            self.input_events.put_nowait(DigitalKeyEvent(t, current_action.id, "down"))
        elif current_action == keymap.hero.strumup:
            # kept sep incase we want to track
            self.input_events.put_nowait(DigitalKeyEvent(t, "strum", "down"))
        elif current_action == keymap.hero.strumdown:
            self.input_events.put_nowait(DigitalKeyEvent(t, "strum", "down"))

    def on_key_release(self, symbol: int, modifiers: int) -> None:
        # ignore spam during front/back porch
        t = self.chart_time
        hit_win = self.hit_window
        if t + hit_win < self.chart.notes[0].time or t - hit_win > self.chart.notes[-1].time:
            return

        current_action = keymap.hero.pressed_action
        if current_action is None:
            return

        if current_action in {keymap.hero.green, keymap.hero.red, keymap.hero.yellow, keymap.hero.blue, keymap.hero.orange}:
            self.input_events.put_nowait(DigitalKeyEvent(t, current_action.id, "up"))

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

        if not self.current_notes:
            return # ! We are out of notes, but we still need to handle sustains hmmmm.


        # Remove all missed chords
        # ! What happens if it was a tap/hopo we could have hit using the last chord?
        # ! Or can we safely assert that would have been caught? I think yes, but lets see.
        while self.current_notes[0].time < self.window_back_end:
            self.miss_chord(self.current_notes[0])

        # ? Could we maybe just check the first valid tap in here ?
        # ? Also if you miss a note does that invalidate the tap ?

        # Process all the note inputs
        while not self.input_events.empty():
            event = self.input_events.get_nowait()
            if event.time < self.window_back_end:
                # Skip events that are now outside the input time.
                # Should only happen after lag spikes or if some inputs are processed
                continue

            if event.time > self.window_front_end:
                # Okay so we are done cause these inputs are in the future????
                # ! THIS SHOULD NEVER HAPPEN AND MAYBE WE SHOULD THROW AND ERROR
                break

            match event.key:
                case "hero_1":
                    self.on_fret_change(Fret.GREEN, event.time)
                case "hero_2":
                    self.on_fret_change(Fret.RED, event.time)
                case "hero_3":
                    self.on_fret_change(Fret.YELLOW, event.time)
                case "hero_4":
                    self.on_fret_change(Fret.BLUE, event.time)
                case "hero_5":
                    self.on_fret_change(Fret.ORANGE, event.time)
                case "strum":
                    self.on_strum(event.time)
                case _:
                    raise ThisShouldNeverHappenError



    def on_fret_change(self, fret: Fret, time: Seconds) -> None:
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

        self.last_chord_shape = chord_shape = last_shape.update_fret(fret)

        if current_chord.time > self.window_front_end:
            # The current chord isn't available to process,
            # but we needed to update the chord shape
            return

        if (time - last_strum) <= self.strum_leniency and current_chord.shape == chord_shape:
            # ! Assumes last strum is before time.
            # ! Doesn't make sense to not be true, but it is an assumption
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
        # No Input Ghosting or Anchoring
        # No Chord Skipping
        # Prolly so much else lmao

        current_chord = self.current_notes[0]
        currnet_shape = self.last_chord_shape
        last_strum = self.last_strum_time

        if time - last_strum <= self.strum_leniency:
            self.overstrum()
            return

        if current_chord.time > self.window_front_end:
            # The current chord isn't available to process,
            # but we needed to process overstrum
            return

        if currnet_shape.matches(current_chord.shape):
            self.hit_chord(current_chord, time)
            self.last_strum_time = -float('inf') # ? Should this just go in hit chord? I think no cause taps
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
