from __future__ import annotations
from typing import Generic, Literal, TypeVar

import math

from charm.lib.types import Seconds
from charm.core.keymap import KeyMap

from .chart import BaseChart, BaseNote
from .judgement import Judgement
from .results import BaseResults, Results

KeyStates = list[bool]
Key = int


class EngineEvent:
    """Any Event that happens at a time. Meant to be subclassed."""
    def __init__(self, time: float):
        self.time = time

    def __lt__(self, other: EngineEvent):
        return self.time < other.time

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} t:{self.time}>"

    def __str__(self) -> str:
        return self.__repr__()


class DigitalKeyEvent[K](EngineEvent):
    """Any input event with a binary state."""
    def __init__(self, time: float, key: K, new_state: Literal["up", "down"]):
        super().__init__(time)
        self.key = key
        self.new_state = new_state

    @property
    def down(self) -> bool:
        return self.new_state == "down"

    def __lt__(self, other: DigitalKeyEvent[K]):
        return (self.time, self.key) < (other.time, other.key)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} key:{self.key}{'⬇️' if self.down else '⬆️'}>"

    def __str__(self) -> str:
        return self.__repr__()


type BaseEngine = Engine[BaseChart, BaseNote]

C = TypeVar("C", bound=BaseChart, covariant=True)
N = TypeVar("N", bound=BaseNote, covariant=True)


class Engine(Generic[C, N]):
    def __init__(self, chart: C, judgements: list[Judgement] | None = None, offset: Seconds = 0):
        """The class that processes user inputs into score according to a Chart."""
        self.chart = chart
        self.offset = offset
        self.judgements: list[Judgement] = judgements or []

        self.chart_time: Seconds = 0
        self.current_notes = list(self.chart.notes)

        # Scoring
        self.score: int = 0
        self.hits: int = 0
        self.misses: int = 0

        # Streak
        self.streak: int = 0
        self.max_streak: int = 0

        # Accuracy
        self.max_notes = len(self.chart.notes)
        self.weighted_hit_notes: float = 0

        # Display
        self.last_note_hit: N | None = None

        self.keystate: tuple[bool, ...] = NotImplemented

    @property
    def window_front_end(self) -> Seconds:
        return self.chart_time + self.hit_window

    @property
    def window_back_end(self) -> Seconds:
        return self.chart_time - self.hit_window

    @property
    def hit_window(self) -> Seconds:
        """The maximum seconds offset from the intended note timing that points can be scored in.
        Works as a kind of first-pass check to see if we should try to score a note.

        Fun fact! This used to be set seperately from the judgements, but that doesn't make sense!
        Why were we doing that?"""
        # NOTE: This will break if there aren't at least two judgements, but if we run into that
        # we should really look into why on Earth we're doing that and what the intended effect is.
        return self.judgements[-2].ms / 1000.0

    def pause(self) -> None:
        pass

    def unpause(self) -> None:
        pass

    @property
    def accuracy(self) -> float:
        if self.hits or self.misses:
            return self.weighted_hit_notes / (self.hits + self.misses)
        return 0

    @property
    def grade(self) -> str:
        accuracy = self.accuracy * 100
        if accuracy is not None:
            if accuracy >= 97.5:
                return "SS"
            elif accuracy >= 95:
                return "S"
            elif accuracy >= 90:
                return "A"
            elif accuracy >= 80:
                return "B"
            elif accuracy >= 70:
                return "C"
            elif accuracy >= 60:
                return "D"
            else:
                return "F"
        return "C"

    @property
    def fc_type(self) -> str:
        if self.accuracy is not None:
            if self.misses == 0:
                if self.grade in {"SS", "S", "A"}:
                    return f"{self.grade}FC"
                else:
                    return "FC"
            elif self.misses < 10:
                return f"SDCB (-{self.misses})"
        return "Clear"

    def update(self, song_time: Seconds) -> None:
        self.chart_time = song_time + self.offset

    def on_button_press(self, keymap: KeyMap) -> None:
        pass
        # TODO: Maybe remove?

    def on_button_release(self, keymap: KeyMap) -> None:
        pass
        # TODO: Maybe remove?

    def calculate_score(self) -> None:
        raise NotImplementedError

    def score_note(self) -> None:
        raise NotImplementedError

    def get_note_judgement(self, note: N) -> Judgement:
        if note.hit_time is None:
            raise RuntimeError
        rt = abs(note.hit_time - note.time)
        # NOTE: This might not be the fast way to get the right judgement,
        # maybe we should switch to an Index?
        for j in self.judgements:
            if rt <= j.seconds:
                return j
        return self.judgements[-1]

    def generate_results(self) -> Results[C]:
        raise NotImplementedError


class AutoEngine(Engine[BaseChart, BaseNote]):
    def __init__(self, chart: BaseChart, offset: float = 0, lanes: int = 4):
        super().__init__(chart,
                         [Judgement("Auto", "auto", chart.notes[-1].end, 0, 0),
                          Judgement("Miss", "miss", float('inf'), 0, 0)],
                          offset)
        self.keystate = (False, ) * lanes

    def calculate_score(self) -> None:
        # Get all non-scored notes within the current window
        for note in [n for n in self.current_notes if n.time <= self.chart_time + self.hit_window]:
            # Missed notes (current time is higher than max allowed time for note)
            # But Digi, that would never happen, this is the auto engine!
            # Trueee, except of course if the game is lagging or there is a skip in the song or something.
            # I think it's worth tracking that.
            if self.chart_time > note.time + self.hit_window:
                note.missed = True
                note.hit_time = math.inf
                self.score_note(note)
                self.current_notes.remove(note)
            # Hit every note
            elif self.chart_time >= note.time:
                note.hit = True
                note.hit_time = note.time
                self.score_note(note)
                self.current_notes.remove(note)
                self.last_note_hit = note

    def score_note(self, note: BaseNote) -> None:
        # Ignore notes we haven't done anything with yet
        if not (note.hit or note.missed):
            return

        if note.hit:
            self.hits += 1
            self.streak += 1
            self.max_streak = max(self.streak, self.max_streak)
        elif note.missed:
            self.misses += 1
            self.streak = 0
