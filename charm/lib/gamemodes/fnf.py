from __future__ import annotations

import importlib.resources as pkg_resources
import json
import logging
import math
from dataclasses import dataclass
from functools import cache
from hashlib import sha1
from pathlib import Path
from typing import Optional, TypedDict, cast

import arcade
import PIL, PIL.ImageFilter

from charm.lib.adobexml import AdobeSprite
from charm.lib.charm import load_missing_texture
from charm.lib.errors import AssetNotFoundError, NoChartsError, UnknownLanesError
from charm.lib.generic.engine import DigitalKeyEvent, Engine, Judgement, KeyStates
from charm.lib.generic.highway import Highway
from charm.lib.generic.song import BPMChangeEvent, Chart, Event, Metadata, Milliseconds, Note, Seconds, Song
from charm.lib.keymap import get_keymap
from charm.lib.logsection import LogSection
from charm.lib.paths import modsfolder
from charm.lib.settings import Settings
from charm.lib.spritebucket import SpriteBucketCollection
from charm.lib.utils import clamp, img_from_resource
from charm.objects.line_renderer import NoteTrail

import charm.data.assets
import charm.data.images.skins.fnf as fnfskin

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
    GREEN = arcade.color.LIME_GREEN
    RED = arcade.color.RED
    PINK = arcade.color.PINK
    BLUE = arcade.color.CYAN
    BOMB = arcade.color.DARK_RED
    DEATH = arcade.color.BLACK
    HEAL = arcade.color.WHITE
    CAUTION = arcade.color.YELLOW

    @classmethod
    def from_note(cls, note: "FNFNote"):
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
            case NoteType.BOMB:
                return cls.BOMB
            case NoteType.DEATH:
                return cls.DEATH
            case NoteType.HEAL:
                return cls.HEAL
            case NoteType.CAUTION:
                return cls.CAUTION
            case _:
                return arcade.color.BLACK


@dataclass
class CameraFocusEvent(Event):
    focused_player: int

@dataclass
class FNFNote(Note):
    parent: FNFNote = None
    sprite: FNFNoteSprite | FNFLongNoteSprite = None

    def __lt__(self, other):
        return (self.time, self.lane, self.type) < (other.time, other.lane, other.type)


class FNFJudgement(Judgement):
    pass
    # @property
    # def image_name(self) -> str:
    #     return f"judge-{self.name}"


class FNFChart(Chart):
    def __init__(self, song: FNFSong, difficulty: str, player: int, speed: float, hash: str):
        super().__init__(song, "fnf", difficulty, f"player{player}", 4, hash)
        self.player1 = "bf"
        self.player2 = "dad"
        self.spectator = "gf"
        self.stage = "stage"
        self.notespeed = speed
        self.hash = hash

        self.notes: list[FNFNote] = []

    def get_current_sustains(self, time: Seconds):
        return [note.lane for note in self.notes if note.is_sustain and note.time <= time and note.end >= time]


class FNFMod:
    def __init__(self, folder_name: str) -> None:
        self.folder_name = folder_name
        self.path = modsfolder / self.folder_name
        self.name: str = None
        self.songs = list[FNFSong]


class FNFSong(Song):
    def __init__(self, song_code: str, mod: FNFMod = None) -> None:
        super().__init__(song_code)
        self.mod: FNFMod = mod
        self.charts: list[FNFChart] = []

    @classmethod
    def get_metadata(cls, folder: Path) -> Metadata:
        """Gets metadata from a chart file."""
        title = folder.stem.replace("-", " ").title()
        artist = ""
        album = ""
        return Metadata(title, artist, album, hash = f"fnf-{title}", path = folder, gamemode = "fnf")

    @classmethod
    def parse(cls, folder: Path, mod: FNFMod = None) -> FNFSong:
        folder_path = Path(folder)
        stem = folder_path.stem
        song = FNFSong(folder)

        charts = song.path.glob(f"./{stem}*.json")
        parsed_charts = [cls.parse_chart(chart, song) for chart in charts]
        for charts in parsed_charts:
            for chart in charts:
                song.charts.append(chart)

        if not song.charts:
            raise NoChartsError(folder)

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
            chart.player1 = songdata.get("player1", "bf")
            chart.player2 = songdata.get("player2", "dad")
            chart.spectator = songdata.get("player3", "gf")
            chart.stage = songdata.get("stage", "stage")

        sections = songdata["song"]

        last_bpm = bpm
        last_focus: Optional[int] = None
        section_start = 0.0
        events: list[Event] = []
        sections = songdata["notes"]
        section_starts = []
        unknown_lanes = []

        # hardcode_search = (h for h in hardcodes if h.hash == returnsong.hash)
        # hardcode = next(hardcode_search, None)

        # if hardcode:
        #     returnsong.metadata["artist"] = hardcode.author
        #     returnsong.metadata["album"] = hardcode.mod_name

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
            section_length = section["lengthInSteps"] * seconds_per_sixteenth

            # Create a camera focus event like they should have in the first place
            if section["mustHitSection"]:
                focused, unfocused = 0, 1
            else:
                focused, unfocused = 1, 0

            if focused != last_focus:
                events.append(CameraFocusEvent(section_start, focused))
                last_focus = focused

            # Lanemap: (player, lane, type)
            # TODO: overrides for this
            if fnf_overrides:
                lanemap = [[l[0], l[1], getattr(NoteType, l[2])] for l in fnf_overrides["lanes"]]
            else:
                lanemap: list[tuple[int, int, NoteType]] = [(0, 0, NoteType.NORMAL), (0, 1, NoteType.NORMAL), (0, 2, NoteType.NORMAL), (0, 3, NoteType.NORMAL),
                                                        (1, 0, NoteType.NORMAL), (1, 1, NoteType.NORMAL), (1, 2, NoteType.NORMAL), (1, 3, NoteType.NORMAL)]
            # Actually make two charts
            sectionNotes = section["sectionNotes"]
            for note in sectionNotes:
                extra = None
                if len(note) > 3:
                    extra = note[3:]
                    note = note[:3]
                posms, lane, lengthms = note  # hope this never breaks lol
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
                    note_player = note_data[0]
                chart_lane = note_data[1]
                note_type = note_data[2]

                thisnote = FNFNote(charts[note_player], pos, chart_lane, length, type = note_type)
                thisnote.extra_data = extra
                if thisnote.type in [NoteType.BOMB, NoteType.DEATH, NoteType.HEAL, NoteType.CAUTION]:
                    thisnote.length = 0  # why do these ever have length?
                if thisnote.length < 0.001:
                    thisnote.length = 0
                charts[note_player].notes.append(thisnote)

                # TODO: Fake sustains (change this?)
                if thisnote.length != 0:
                    sustainbeats = round(thisnote.length / seconds_per_sixteenth)
                    for i in range(sustainbeats):
                        j = i + 1
                        thatnote = FNFNote(charts[note_player], pos + (seconds_per_sixteenth * (i + 1)), chart_lane, 0, "sustain")
                        thatnote.parent = thisnote
                        charts[note_player].notes.append(thatnote)

            section_start += section_length

        for c in charts:
            c.events = events
            c.notes.sort()
            c.events.sort()
            logger.debug(f"Parsed chart {c.instrument} with {len(c.notes)} notes.")

        unknown_lanes = sorted(set(unknown_lanes))
        if unknown_lanes:
            raise UnknownLanesError(f"Unknown lanes found in chart {name}: {unknown_lanes}")

        return charts

    def get_chart(self, player, difficulty):
        return next((c for c in self.charts if c.difficulty == difficulty and c.instrument == f"player{player}"), None)


class FNFEngine(Engine):
    def __init__(self, chart: FNFChart, offset: Seconds = -0.075):  # FNF defaults to a 75ms input offset.
        hit_window = 0.166
        fk = get_keymap().get_set("fourkey")
        mapping = [fk.key1, fk.key2, fk.key3, fk.key4]
        judgements = [
            #           ("name",  "key"    ms,       score, acc,   hp=0)
            FNFJudgement("sick",  "sick",  45,       350,   1,     0.04),
            FNFJudgement("good",  "good",  90,       200,   0.75),
            FNFJudgement("bad",   "bad",   135,      100,   0.5,  -0.03),
            FNFJudgement("awful", "awful", 166,      50,    -1,   -0.06),  # I'm not calling this "s***", it's not funny.
            FNFJudgement("miss",  "miss",  math.inf, 0,     -1,   -0.1)
        ]
        super().__init__(chart, mapping, hit_window, judgements, offset)

        self.min_hp = 0
        self.hp = 1
        self.max_hp = 2
        self.bomb_hp = 0.5
        self.heal_hp = 0.5

        self.has_died = False

        self.latest_judgement = ""
        self.latest_judgement_time = 0
        self.all_judgements: list[tuple[Seconds, Seconds, Judgement]] = []

        self.current_notes: list[FNFNote] = self.chart.notes.copy()
        self.current_events: list[DigitalKeyEvent] = []

        self.last_p1_note = None
        self.last_note_missed = False

    def process_keystate(self, key_states: KeyStates):
        last_state = self.key_state
        if self.last_p1_note in (0, 1, 2, 3) and key_states[self.last_p1_note] is False:
            self.last_p1_note = None
        # ignore spam during front/back porch
        if (self.chart_time < self.chart.notes[0].time - self.hit_window
           or self.chart_time > self.chart.notes[-1].time + self.hit_window):
            return
        for n in range(len(key_states)):
            if key_states[n] is True and last_state[n] is False:
                e = DigitalKeyEvent(self.chart_time, n, "down")
                self.current_events.append(e)
            elif key_states[n] is False and last_state[n] is True:
                e = DigitalKeyEvent(self.chart_time, n, "up")
                self.current_events.append(e)
        self.key_state = key_states.copy()

    def calculate_score(self):
        # Get all non-scored notes within the current window
        for note in [n for n in self.current_notes if n.time <= self.chart_time + self.hit_window]:
            # Missed notes (current time is higher than max allowed time for note)
            if self.chart_time > note.time + self.hit_window:
                note.missed = True
                note.hit_time = math.inf  # how smart is this? :thinking:
                self.score_note(note)
                self.current_notes.remove(note)
            else:
                if note.type == "sustain":
                    if self.key_state[note.lane]:
                        note.hit = True
                        note.hit_time = note.time
                        self.score_note(note)
                        self.current_notes.remove(note)
                # Check non-used events to see if one matches our note
                for event in [e for e in self.current_events if e.new_state == "down"]:
                    # We've determined the note was hit
                    if event.key == note.lane and abs(event.time - note.time) <= self.hit_window:
                        note.hit = True
                        note.hit_time = event.time
                        self.score_note(note)
                        try:
                            self.current_notes.remove(note)
                        except ValueError:
                            logger.info("Sustain pickup failed!")
                        self.current_events.remove(event)
                        break

        # Make sure we can't go below min_hp or above max_hp
        self.hp = clamp(self.min_hp, self.hp, self.max_hp)
        if self.hp == self.min_hp:
            self.has_died = True

    def score_note(self, note: FNFNote):
        # Ignore notes we haven't done anything with yet
        if not (note.hit or note.missed):
            return

        # Sustains use different scoring
        if note.type == "sustain":
            self.last_p1_note = note.lane
            if note.hit:
                self.hp += 0.02
                self.last_note_missed = False
                note.parent.sprite.dead = False
            elif note.missed:
                self.hp -= 0.05
                self.last_note_missed = True
                note.parent.sprite.dead = True
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
            return

        # Score the note
        j = self.get_note_judgement(note)
        self.score += j.score
        self.weighted_hit_notes += j.accuracy_weight

        # Give HP for hit note (heal notes give more)
        if note.type == "heal":
            self.hp += self.heal_hp
        else:
            self.hp += j.hp_change

        # Judge the player
        rt = abs(note.hit_time - note.time)
        self.latest_judgement = j.name
        self.latest_judgement_time = self.chart_time
        self.all_judgements.append((self.latest_judgement_time, rt, self.latest_judgement))

        # Animation and hit/miss tracking
        self.last_p1_note = note.lane
        if note.hit:
            self.hits += 1
            self.last_note_missed = False
        elif note.missed:
            self.misses += 1
            self.last_note_missed = True


@cache
def load_note_texture(note_type, note_lane, height):
    image_name = f"{note_type}-{note_lane + 1}"
    try:
        image = img_from_resource(fnfskin, image_name + ".png")
        if image.height != height:
            width = int((height / image.height) * image.width)
            image = image.resize((width, height), PIL.Image.LANCZOS)
    except Exception:
        logger.error(f"Unable to load texture: {image_name}")
        return load_missing_texture(height, height)
    return arcade.Texture(image)


class FNFNoteSprite(arcade.Sprite):
    def __init__(self, note: FNFNote, highway: FNFHighway, height = 128, *args, **kwargs):
        self.note: FNFNote = note
        self.note.sprite = self
        self.highway: FNFHighway = highway
        tex = load_note_texture(note.type, note.lane, height)
        super().__init__(tex, *args, **kwargs)
        if self.note.type == "sustain":
            self.alpha = 0

    def __lt__(self, other: FNFNoteSprite):
        return self.note.time < other.note.time

    def update_animation(self, delta_time: float):
        if self.highway.auto:
            if self.highway.song_time >= self.note.time:
                self.note.hit = True
        # if self.note.hit and self.highway.song_time >= self.note.time:
        #     self.alpha = 0
        if self.note.hit:
            self.alpha = 0


class FNFLongNoteSprite(FNFNoteSprite):
    id = 0

    def __init__(self, note: FNFNote, highway: FNFHighway, height=128, *args, **kwargs):
        super().__init__(note, highway, height, *args, **kwargs)
        self.id += 1
        self.dead = False

        color = NoteColor.from_note(self.note)
        self.trail = NoteTrail(self.id, self.position, self.note.time, self.note.length, self.highway.px_per_s,
        color, width = self.highway.note_size, upscroll = True, fill_color = color[:3] + (60,), resolution = 100)
        self.dead_trail = NoteTrail(self.id, self.position, self.note.time, self.note.length, self.highway.px_per_s,
        arcade.color.GRAY, width = self.highway.note_size, upscroll = True, fill_color = arcade.color.GRAY[:3] + (60,), resolution = 100)

    def update_animation(self, delta_time: float):
        self.trail.set_position(*self.position)
        self.dead_trail.set_position(*self.position)
        return super().update_animation(delta_time)

    def draw_trail(self):
        self.dead_trail.draw() if self.dead else self.trail.draw()


class FNFHighway(Highway):
    def __init__(self, chart: FNFChart, engine: FNFEngine, pos: tuple[int, int], size: tuple[int, int] = None, gap: int = 5, auto = False):
        if size is None:
            size = int(Settings.width / (1280 / 400)), Settings.height

        super().__init__(chart, pos, size, gap)

        self.engine = engine

        self.viewport = 1 / (chart.notespeed * 0.75)

        self.auto = auto

        self.sprite_buckets = SpriteBucketCollection()
        for note in self.notes:
            sprite = FNFNoteSprite(note, self, self.note_size) if note.length == 0 else FNFLongNoteSprite(note, self, self.note_size)
            sprite.top = self.note_y(note.time)
            sprite.left = self.lane_x(note.lane)
            note.sprite = sprite
            self.sprite_buckets.append(sprite, note.time, note.length)
        logger.debug(f"Sustains: {len([s for s in self.sprite_buckets.sprites if isinstance(s, FNFLongNoteSprite)])}")

        self.strikeline = arcade.SpriteList()
        for i in [0, 1, 2, 3]:
            sprite = FNFNoteSprite(FNFNote(self.chart, 0, i, 0, "strikeline"), self, self.note_size)
            sprite.top = self.strikeline_y
            sprite.left = self.lane_x(sprite.note.lane)
            sprite.alpha = 64
            self.strikeline.append(sprite)

        self.hit_window_mid = self.note_y(0) - (self.note_size / 2)

        logger.debug(f"Generated highway for chart {chart.instrument}.")

        # TODO: Replace with better pixel_offset calculation
        self.last_update_time = 0
        self._pixel_offset = 0

    def update(self, song_time: float):
        super().update(song_time)
        self.sprite_buckets.update_animation(song_time)
        # TODO: Replace with better pixel_offset calculation
        delta_draw_time = self.song_time - self.last_update_time
        self._pixel_offset += (self.px_per_s * delta_draw_time)
        self.last_update_time = self.song_time

        self.highway_camera.move((0.0, -self.pixel_offset))
        self.highway_camera.update()

    @property
    def pixel_offset(self):
        # TODO: Replace with better pixel_offset calculation
        return self._pixel_offset

    def draw(self):
        _cam = arcade.get_window().current_camera
        self.static_camera.use()
        self.strikeline.draw()
        self.highway_camera.use()
        # This is slow, don't loop over things.
        b = self.sprite_buckets.calc_bucket(self.song_time)
        window = arcade.get_window()
        for bucket in self.sprite_buckets.buckets[b:b+2] + [self.sprite_buckets.overbucket]:
            for note in bucket.sprite_list:
                if isinstance(note, FNFLongNoteSprite) and note.note.time < self.song_time + self.viewport:
                    # Clip the rendering to the strikeline if the key is being held.
                    if self.engine.key_state[note.note.lane] or self.auto:
                        window.ctx.scissor = (0, 0, window.width, self.hit_window_mid)
                    else:
                        window.ctx.scissor = None
                    note.draw_trail()
                window.ctx.scissor = None
        self.sprite_buckets.draw(self.song_time)
        _cam.use()


class FNFAssetManager:
    def __init__(self, song: FNFSong):
        self.song = song

    def load_asset(self, asset_type: str, name: str, default: str = None, *, anchors: list[str] = ["bottom"]) -> AdobeSprite | arcade.Sprite:
        sub_path = f"{asset_type}/{name}.png"
        possiblepaths: list[Path] = []
        # Path to asset if it's in the song folder
        possiblepaths.append(self.song.path / "assets" / sub_path)
        # Path to asset if it's in the mod folder (and y'know, the mod exists)
        if self.song.mod is not None:
            possiblepaths.append(self.song.mod.path / "assets" / sub_path)
        # Path to asset if it's in the game files
        with pkg_resources.path(charm.data.assets, "__init__.py") as p:
            builtin_assets = p.parent
            possiblepaths.append(builtin_assets / sub_path)
        # Path to asset if it's the default
        if default:
            possiblepaths.append(builtin_assets / f"{asset_type}/{default}.png")

        try:
            path = next(p for p in possiblepaths if p.exists())
        except StopIteration:
            raise AssetNotFoundError(name)

        xml_path = path.parent / f"{path.stem}.xml"
        if xml_path.exists():
            return AdobeSprite(xml_path.parent, path.stem, anchors)
        else:
            return arcade.Sprite(path)


class FNFSceneManager:
    """Controls the display of the FNF scene.
       Handles sprite loading, most rendering, and inter-element interactions.

       `chart: FNFChart`: the chart the player is currenty playing."""
    def __init__(self, chart: FNFChart):
        self.chart = chart
        self.song: FNFSong = cast(FNFSong, chart.song)

        self.enemy_chart = self.song.get_chart(2, self.chart.difficulty)

        with LogSection(logger, "asset manager init"):
            self.assetmanager = FNFAssetManager(self.song)
            # function alias
            self.load_asset = self.assetmanager.load_asset

        with LogSection(logger, "creating engine"):
            self.engine = FNFEngine(self.chart)

        with LogSection(logger, "creating highways"):
            self.highway_1 = FNFHighway(self.chart, self.engine, (((Settings.width // 3) * 2), 0))
            self.highway_2 = FNFHighway(self.enemy_chart, self.engine, (10, 0), auto=True)

        with LogSection(logger, "loading assets"):
            # Characters
            self.player_sprite = self.load_asset("characters", self.chart.player1, "boyfriend")
            # self.spectator_sprite = self.load_asset("characters", self.chart.spectator, "girlfriend")
            # self.enemy_sprite = self.load_asset("characters", self.chart.player2, "dad")

            # self.stage = self.load_asset("stages", self.chart.stage)

            # Categories
            self.characters = [self.player_sprite]

    def update(self, song_time: Seconds, delta_time: Seconds):
        self.engine.update(song_time)

        # TODO: Lag? Maybe not calculate this every tick?
        # The only way to solve this I think is to create something like an
        # on_note_valid and on_note_expired event, which you can do with
        # Arcade.schedule() if we need to look into that.
        self.engine.calculate_score()

        self.highway_1.update(song_time)
        self.highway_2.update(song_time)

        for c in self.characters:
            c.update_animation(delta_time)
