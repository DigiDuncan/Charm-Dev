from __future__ import annotations

from importlib.resources import files, as_file
import json
import logging
import math
from dataclasses import dataclass
from hashlib import sha1
from pathlib import Path
from typing import TypedDict

import arcade
from arcade import Texture, Sprite, draw_sprite, Text, color as colors
from arcade.types import Color

from charm.lib.errors import NoChartsError, UnknownLanesError, ChartPostReadParseError
from charm.lib.gamemodes.four_key import FourKeyChart, FourKeyEngine, FourKeyJudgement, FourKeyNote, FourKeyHighway
from charm.lib.generic.engine import Engine, AutoEngine
from charm.lib.anim import ease_circout, perc
from charm.lib.generic.song import BPMChangeEvent, Event, Metadata, Song
from charm.lib.generic.display import Display
from charm.lib.types import Seconds, Milliseconds
from charm.lib.utils import clamp
import charm.data.images.skins as skins
from charm.objects.lyric_animator import LyricEvent
from charm.lib.keymap import keymap

logger = logging.getLogger("charm")


class SongFileJson(TypedDict):
    song: SongJson


class SongJson(TypedDict):
    song: str
    bpm: float
    speed: float
    notes: list[NoteJson]


class NoteJson(TypedDict):
    bpm: float
    mustHitSection: bool
    sectionNotes: list[tuple[Milliseconds, int, Milliseconds]]
    lengthInSteps: int


class NoteType:
    NORMAL = "normal"
    BOMB = "bomb"
    DEATH = "death"
    HEAL = "heal"
    CAUTION = "caution"


class NoteColor:
    GREEN = colors.LIME_GREEN
    RED = colors.RED
    PINK = colors.PINK
    BLUE = colors.CYAN
    BOMB = colors.DARK_RED
    DEATH = colors.BLACK
    HEAL = colors.WHITE
    CAUTION = colors.YELLOW

    @classmethod
    def from_note(cls, note: FNFNote) -> Color:
        match note.type:
            case NoteType.NORMAL:
                if note.lane == 0:
                    return cls.PINK
                elif note.lane == 1:
                    return cls.BLUE
                elif note.lane == 2:
                    return cls.GREEN
                elif note.lane == 3:
                    return cls.RED
                else:
                    return colors.BLACK
            case NoteType.BOMB:
                return cls.BOMB
            case NoteType.DEATH:
                return cls.DEATH
            case NoteType.HEAL:
                return cls.HEAL
            case NoteType.CAUTION:
                return cls.CAUTION
            case _:
                return colors.BLACK


@dataclass
class CameraFocusEvent(Event):
    focused_player: int

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}@{self.time:.3f} p:{self.focused_player}>"

    def __str__(self) -> str:
        return self.__repr__()


@dataclass(repr = False)
class FNFNote(FourKeyNote):
    parent: FNFNote = None

    def __lt__(self, other):
        return (self.time, self.lane, self.type) < (other.time, other.lane, other.type)


class FNFJudgement(FourKeyJudgement):
    def get_texture(self) -> Texture:
        with as_file(files(skins) / "fnf" / f"judgement-{self.key}.png") as p:
            tex = arcade.load_texture(p)
        return tex


class FNFChart(FourKeyChart):
    def __init__(self, song: FNFSong, difficulty: str, player: int, speed: float, hash: str | None):
        super().__init__(song, difficulty, hash)
        self.player1 = "bf"
        self.player2 = "dad"
        self.spectator = "gf"
        self.stage = "stage"
        self.notespeed = speed
        self.hash = hash

        self.instrument = f"fnf-player{player}"

        self.notes: list[FNFNote] = []

    def get_current_sustains(self, time: Seconds) -> list[int]:
        return [note.lane for note in self.notes if note.is_sustain and note.time <= time and note.end >= time]


class FNFSong(Song[FNFChart]):
    def __init__(self, song_code: str) -> None:
        super().__init__(song_code)

    @classmethod
    def get_metadata(cls, folder: Path) -> Metadata:
        """Gets metadata from a chart file."""
        title = folder.stem.replace("-", " ").title()
        return Metadata(path=folder, title=title, hash=f"fnf-{title}", gamemode="fnf")

    @classmethod
    def parse(cls, path: Path) -> FNFSong:
        folder_path = Path(path)
        stem = folder_path.stem
        song = FNFSong(path)

        charts = song.path.glob(f"./{stem}*.json")
        parsed_charts = [cls.parse_chart(chart, song) for chart in charts]
        if len(parsed_charts) == 0:
            raise NoChartsError(path.stem)
        for charts in parsed_charts:
            for chart in charts:
                song.charts.append(chart)

        # Global attributes that are stored per-chart, for some reason.
        chart: FNFChart = song.charts[0]
        song.bpm = chart.bpm
        song.metadata.title = chart.name

        return song

    @classmethod
    def parse_chart(cls, path: Path, song: FNFSong) -> list[FNFChart]:
        with open(path) as p:
            j: SongFileJson = json.load(p)
        fnf_overrides = None
        override_path = path.parent / "fnf.json"
        if override_path.exists() and override_path.is_file():
            with open(override_path) as f:
                fnf_overrides = json.load(f)
        hash = sha1(bytes(json.dumps(j), encoding="utf-8")).hexdigest()
        difficulty = path.stem.rsplit("-", 1)[1] if "-" in path.stem else "normal"
        songdata = j["song"]

        name = songdata["song"].replace("-", " ").title()
        logger.debug(f"Parsing {name}...")
        bpm = songdata["bpm"]
        speed = songdata["speed"]
        charts = [
            FNFChart(song, difficulty, 1, speed, hash),
            FNFChart(song, difficulty, 2, speed, hash)]

        for chart in charts:
            chart.name = songdata["song"]
            chart.bpm = bpm
            # These properties are only used for FNF visuals, which I don't support at the
            # moment but might be useful metadata anyway.
            chart.player1 = songdata.get("player1", "bf")
            chart.player2 = songdata.get("player2", "dad")
            chart.spectator = songdata.get("player3", "gf")
            chart.stage = songdata.get("stage", "stage")

        sections = songdata["song"]  # Unused

        last_bpm = bpm
        last_focus: int | None = None
        section_start = 0.0
        events: list[Event] = []
        sections = songdata["notes"]
        section_starts = []
        unknown_lanes = []

        for section in sections:
            # There's a changeBPM event but like, it always has to be paired
            # with a bpm, so it's pointless anyway
            if "bpm" in section:
                new_bpm = section["bpm"]
                if new_bpm != last_bpm:
                    events.append(BPMChangeEvent(section_start, new_bpm))
                    last_bpm = new_bpm
            section_starts.append((section_start, bpm))

            # Since in theory you can have events in these sections
            # without there being notes there, I need to calculate where this
            # section occurs from scratch, and some engines have a startTime
            # thing here but I can't guarantee it so it's basically pointless
            seconds_per_beat = 60 / bpm
            seconds_per_measure = seconds_per_beat * 4
            seconds_per_sixteenth = seconds_per_measure / 16
            if "lengthInSteps" in section:
                section_length = section["lengthInSteps"] * seconds_per_sixteenth
            elif "sectionBeats" in section:
                section_length = section["sectionBeats"] * seconds_per_sixteenth * 4  # Psych Engine recommends this now! yay /s
            else:
                raise ChartPostReadParseError("Notes section missing length!")

            # Create a camera focus event like they should have in the first place
            # mustHitSection indicates the "active player" is the real player (P1).
            # All this really controls is the camera, (because despite the name you have
            # to hit all the notes in all sections), but has the side effect of flipping
            # what lane corrosponds to what player. I fix this by treating the chart's
            # "player 0" to mean "the focused player".
            if section["mustHitSection"]:
                focused, unfocused = 0, 1
            else:
                focused, unfocused = 1, 0

            if focused != last_focus:
                events.append(CameraFocusEvent(section_start, focused))
                last_focus = focused

            # Lanemap: (player, lane, type)
            if fnf_overrides:
                # This is done because some mods use "extra lanes" differents, so I have to provide
                # a file that maps them to the right lane.
                lanemap = [[lane[0], lane[1], getattr(NoteType, lane[2])] for lane in fnf_overrides["lanes"]]
            else:
                lanemap: list[tuple[int, int, NoteType]] = [(0, 0, NoteType.NORMAL), (0, 1, NoteType.NORMAL), (0, 2, NoteType.NORMAL), (0, 3, NoteType.NORMAL),
                                                            (1, 0, NoteType.NORMAL), (1, 1, NoteType.NORMAL), (1, 2, NoteType.NORMAL), (1, 3, NoteType.NORMAL)]
            # Actually make two charts
            section_notes = section["sectionNotes"]
            for note in section_notes:
                extra = None
                if len(note) > 3:
                    extra = note[3:]
                    note = note[:3]
                posms, lane, lengthms = note  # hope this never breaks lol
                # EDIT: It does break, sometimes!
                if lane < 0:
                    continue  # I don't know what to do with these yet.
                pos = posms / 1000
                length = lengthms / 1000

                try:
                    note_data = lanemap[lane]
                except IndexError:
                    unknown_lanes.append(lane)
                    continue

                if note_data[0] == 0:
                    note_player = focused
                elif note_data[0] == 1:
                    note_player = unfocused
                else:
                    note_player = note_data[0]  # If the note_player isn't 0/1, this is going to break, realistically, but we want to know that.
                chart_lane = note_data[1]
                note_type = note_data[2]

                thisnote = FNFNote(charts[note_player], pos, chart_lane, length, type = note_type)
                thisnote.extra_data = extra  # Append that data we don't know what to do with, in case one day we do
                if thisnote.type in [NoteType.BOMB, NoteType.DEATH, NoteType.HEAL, NoteType.CAUTION]:
                    thisnote.length = 0  # why do these ever have length?
                if thisnote.length < 0.001:
                    thisnote.length = 0
                charts[note_player].notes.append(thisnote)

                # TODO: Fake sustains (change this?)
                # We basically generate an invisible "sustain" note every 16th-beat. The original game does it
                # but I wish we were doing something better than this, like just doing sustain calculation in-engine
                # while a sustain is active.
                if thisnote.length != 0:
                    sustainbeats = round(thisnote.length / seconds_per_sixteenth)
                    for i in range(sustainbeats):
                        j = i + 1
                        thatnote = FNFNote(charts[note_player], pos + (seconds_per_sixteenth * (i + 1)), chart_lane, 0, "sustain")
                        thatnote.parent = thisnote
                        charts[note_player].notes.append(thatnote)

            section_start += section_length

        # Pysch Engine events look like this
        if "events" in songdata:
            events = songdata["events"]
            for e in events:
                time = e[0] / 1000
                subevents = e[1]
                for s in subevents:
                    t, d1, d2 = s
                    if t == "lyrics":
                        song.lyrics.append(LyricEvent(time, None, d1))

            # Psych Engine lyrics
            if song.lyrics:
                song.lyrics[-1].length = math.inf
                for n, lyric_event in enumerate(song.lyrics[:-1]):
                    lyric_event.length = song.lyrics[n + 1].time - lyric_event.time

        for c in charts:
            c.events = events
            c.notes.sort()
            c.events.sort()
            logger.debug(f"Parsed chart {c.instrument} with {len(c.notes)} notes.")

        unknown_lanes = sorted(set(unknown_lanes))
        if unknown_lanes:
            raise UnknownLanesError(f"Unknown lanes found in chart {name}: {unknown_lanes}")

        return charts

    def get_chart(self, player: str, difficulty: str) -> FNFChart:
        return next((c for c in self.charts if c.difficulty == difficulty and c.instrument == f"fnf-player{player}"), None)


class FNFEngine(FourKeyEngine):
    def __init__(self, chart: FNFChart, offset: Seconds = 0):
        hit_window = 0.166
        judgements = [
            #           ("name",  "key"    ms,       score, acc,   hp=0)
            FNFJudgement("sick",  "sick",  45,       350,   1,     0.04),
            FNFJudgement("good",  "good",  90,       200,   0.75),
            FNFJudgement("bad",   "bad",   135,      100,   0.5,  -0.03),
            FNFJudgement("awful", "awful", 166,      50,    -1,   -0.06),  # I'm not calling this "s***", it's not funny.
            FNFJudgement("miss",  "miss",  math.inf, 0,     -1,   -0.1)
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
        rt = note.hit_time - note.time
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

class FNFDisplay(Display[FNFEngine]):

    def __init__(self, window, engine: FNFEngine, charts: tuple[FNFChart, ...]):
        super().__init__(window, engine, charts)
        # TODO: make more flexible post mvp
        self._enemy_engine: Engine = AutoEngine(charts[1], 0.166)

        # NOTE: change highways to work of their center position not bottom left
        # TODO: fix weird highway offset
        self._player_highway: FourKeyHighway = FourKeyHighway(charts[0], engine, (self._win.width / 3 * 2, 0))
        self._enemy_highway: FourKeyHighway = FourKeyHighway(charts[1], self._enemy_engine, (0, 0))

        # -- Text Objects --
        self.show_text: bool = True
        self._overlay_text: Text = Text("PAUSE", (self._win.width // 2), 10, font_size=24,
                                        anchor_x="center", color=colors.BLACK,
                                        font_name="bananaslip plus")
        self._time_text: Text = Text("??:??", self._win.center_x, 10, font_size=24,
                                     anchor_x="center", color=colors.BLACK,
                                     font_name="bananaslip plus")
        self._score_text: Text = Text("0", self._win.center_x, self._win.height - 10, font_size=24,
                                    anchor_x="center", anchor_y="top", color=colors.BLACK,
                                    font_name="bananaslip plus")
        self._grade_text: Text = Text("Clear", self._win.center_x, self._win.height - 135, font_size=16,
                                      anchor_x="center", anchor_y="center", color=colors.BLACK,
                                      font_name="bananaslip plus")

        # -- Judgement --
        # TODO: move to skinning
        self._judgement_textures: dict[str, Texture] = {
            judgement.key: arcade.load_texture(files(skins) / "fnf" / f"judgement-{judgement.key}.png")
            for judgement in self._engine.judgements
        }

        self._judgement_sprite: Sprite = Sprite(self._judgement_textures[self._engine.judgements[0].key])
        self._judgement_sprite.scale = 0.8 * (self._player_highway.w / self._judgement_sprite.width)
        self._judgement_sprite.alpha = 0
        self._judgement_jump: float = self._win.center_y + 25
        self._judgement_land: float = self._win.center_y

        # TODO: Lyrics

        # -- Camera Events
        self._last_camera_event: CameraFocusEvent = CameraFocusEvent(0, 2)
        self._last_spotlight_position: int = 0
        self.last_spotlight_change: int = 0
        self.go_to_spotlight_position: int = 0
        self.spotlight_position: int = 0
        self.camera_events: list[CameraFocusEvent] = [e for e in charts[0].events if isinstance(e, CameraFocusEvent)]

        self.hp_bar_length = 250
        self._song_time: float = 0.0

    def pause(self) -> None:
        if not self._engine.has_died:
            self._overlay_text.text = "PAUSED"

    def update(self, song_time: Seconds) -> None:
        self._song_time = song_time

        # TODO: Chroma Key

        time_str = f"{int(song_time // 60)}:{int(song_time % 60):02}"
        if self._time_text.text != time_str:
            self._time_text.text = time_str
        if self._score_text.text != str(self._engine.score):
            self._score_text.text = str(self._engine.score)

        self._enemy_engine.update(song_time)
        self._enemy_engine.calculate_score()

        self._player_highway.update(song_time)
        self._enemy_highway.update(song_time)

        if self._engine.latest_judgement_time:
            time = self._engine.latest_judgement_time
            self._judgement_sprite.texture = self._judgement_textures[self._engine.latest_judgement.key]
            self._judgement_sprite.center_y = ease_circout(self._judgement_jump, self._judgement_land, perc(time, time + 0.25, song_time))
            self._judgement_sprite.alpha = int(ease_circout(255, 0, perc(time + 0.5, time + 1, song_time)))

        if self._engine.accuracy is not None:
            self._grade_text.text = f"{self._engine.fc_type} | {round(self._engine.accuracy * 100, 2)}% ({self._engine.grade})"

        # TODO: timer
        # TODO: Spotlight

    def draw(self) -> None:
        if self.show_text:
            self._time_text.draw()
            self._score_text.draw()
            if self._engine.has_died:
                self._overlay_text.text = "DEAD"
                self._overlay_text.draw()

        self._player_highway.draw()
        self._enemy_highway.draw()

        self._grade_text.draw()

        draw_sprite(self._judgement_sprite)

        # TODO: Like litterally eveything else

