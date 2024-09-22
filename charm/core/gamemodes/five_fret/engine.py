from collections import defaultdict
from queue import Queue

from charm.lib.errors import TODOError

from charm.core.generic.engine import DigitalKeyEvent
from charm.lib.keymap import keymap
from charm.lib.types import Seconds

from charm.core.generic import Engine, EngineEvent, Judgement
from .chart import ChordShape, FiveFretChart, FiveFretNote, FiveFretChord



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

        self.chord_events: Queue[ChordShapeChangeEvent] = Queue()
        self.strum_events: Queue[DigitalKeyEvent] = Queue()

        self.last_event_times = defaultdict(None)
        self.last_chord_shape: ChordShape = EMPTY_CHORD

        self.infinite_front_end = False
        self.hopo_leniency: Seconds = 0.080
        self.strum_leniency: Seconds = 0.060
        self.no_note_leniency: Seconds = 0.030
        self.sustain_end_leniency: Seconds = 0.01

        self.strum_time: Seconds = -float('inf')

        # todo: ignore overstrum during countdown events

    @property
    def window_front_end(self) -> Seconds:
        return self.chart_time + self.hit_window

    @property
    def window_back_end(self) -> Seconds:
        return self.chart_time - self.hit_window

    def on_strum(self):
        # When a player strums a few things can occur:
        # 1) No strum has happened recently
        #   1 a) No notes are around for it to be a valid strum
        #   1 b) Add the strum to the queue to be processed next update
        # 2) A strum has happened recently -> Mark it as overstrum
        # 3) We are in a countdown so ignore it
        pass

    def on_chord_change(self):
        pass

    def on_whammy(self):
        raise TODOError('Dragon/Digi needs to add whammy')

    def on_starpower(self):
        raise TODOError('Dragon/Digi needs to do Starpower')

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
            shape = ChordShape(
                keymap.hero.green.held,
                keymap.hero.red.held,
                keymap.hero.yellow.held,
                keymap.hero.blue.held,
                keymap.hero.orange.held
            )
            self.chord_events.put_nowait(ChordShapeChangeEvent(t, shape))
            self.last_chord_shape = shape
            self.last_event_times[current_action] = t
        elif current_action == keymap.hero.strumup:
            self.strum_events.put_nowait(DigitalKeyEvent(t, "strumup", "down"))
            self.last_event_times['strum'] = t
        elif current_action == keymap.hero.strumdown:
            self.strum_events.put_nowait(DigitalKeyEvent(t, "strumdown", "down"))
            self.last_event_times['strum'] = t

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
            self.chord_events.put_nowait(ChordShapeChangeEvent(self.chart_time, ChordShape(
                keymap.hero.green.held,
                keymap.hero.red.held,
                keymap.hero.yellow.held,
                keymap.hero.blue.held,
                keymap.hero.orange.held
            )))

            self.last_event_times[symbol] = None

    def pause(self) -> None:
        pass

    def unpause(self) -> None:
        pass

    def calculate_score(self) -> None:
        for chord in self.current_notes[:]:
            if self.window_front_end < chord.time:
                # If the chord is outside the hit window then we have processed all hit able notes
                break

            if self.window_back_end > chord.time:
                # If the note has left the hit window without being it then it is missed
                chord.missed = True
                chord.hit_time = float('inf')
                self.score_chord(chord)
                self.current_notes.remove(chord)
            else:
                pass


    def score_chord(self, chord: FiveFretChord) -> None:
        raise NotImplementedError

    def score_tap(self, chord: FiveFretChord) -> None:
        raise NotImplementedError

    def score_sustain(self, note: FiveFretNote) -> None:
        raise NotImplementedError

    def overstrum(self) -> None:
        pass

    # def generate_results(self) -> Results[C]:
    #     raise NotImplementedError
