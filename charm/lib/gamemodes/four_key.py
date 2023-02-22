from __future__ import annotations

import importlib.resources as pkg_resources
import logging
import math
from dataclasses import dataclass
from functools import cache
from statistics import mean

import arcade
import PIL
import PIL.ImageFilter

import charm.data.images.skins.fnf as fnfskin
import charm.data.images.skins.base as baseskin
from charm.lib.charm import load_missing_texture
from charm.lib.generic.engine import DigitalKeyEvent, Engine, Judgement
from charm.lib.generic.highway import Highway
from charm.lib.generic.results import Results
from charm.lib.generic.song import Note, Chart, Seconds, Song
from charm.lib.keymap import get_keymap
from charm.lib.settings import Settings
from charm.lib.spritebucket import SpriteBucketCollection
from charm.lib.utils import img_from_resource, clamp
from charm.objects.line_renderer import NoteTrail

logger = logging.getLogger("charm")

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
    def from_note(cls, note: "FourKeyNote"):
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
    return arcade.Texture(f"_fnfnote_{image_name}", image=image, hit_box_algorithm=None)

@dataclass
class FourKeyNote(Note):
    parent: FourKeyNote = None
    sprite: "FourKeyNoteSprite" | "FourKeyLongNoteSprite" = None

    def __lt__(self, other):
        return (self.time, self.lane, self.type) < (other.time, other.lane, other.type)

class FourKeyChart(Chart):
    def __init__(self, song: 'Song', difficulty, hash: str):
        super().__init__(song, "4k", difficulty, "4k", 4, hash)
        self.song: FourKeySong = song

class FourKeySong(Song):
    pass

class FourKeyNoteSprite(arcade.Sprite):
    def __init__(self, note: FourKeyNote, highway: FourKeyHighway, height=128, *args, **kwargs):
        self.note: FourKeyNote = note
        self.note.sprite = self
        self.highway: FourKeyHighway = highway
        tex = load_note_texture(note.type, note.lane, height)
        super().__init__(texture=tex, *args, **kwargs)
        if self.note.type == "sustain":
            self.alpha = 0

    def __lt__(self, other: FourKeyNoteSprite):
        return self.note.time < other.note.time

    def update_animation(self, delta_time: float):
        if self.highway.auto:
            if self.highway.song_time >= self.note.time:
                self.note.hit = True
        # if self.note.hit and self.highway.song_time >= self.note.time:
        #     self.alpha = 0
        if self.note.hit:
            self.alpha = 0

class FourKeyLongNoteSprite(FourKeyNoteSprite):
    id = 0

    def __init__(self, note: FourKeyNote, highway: FourKeyHighway, height=128, *args, **kwargs):
        super().__init__(note, highway, height, *args, **kwargs)
        self.id += 1
        self.dead = False

        color = NoteColor.from_note(self.note)
        self.trail = NoteTrail(self.id, self.position, self.note.time, self.note.length, self.highway.px_per_s,
        color, width=self.highway.note_size, upscroll=True, fill_color=color[:3] + (60,), resolution=100)
        self.dead_trail = NoteTrail(self.id, self.position, self.note.time, self.note.length, self.highway.px_per_s,
        arcade.color.GRAY, width=self.highway.note_size, upscroll=True, fill_color=arcade.color.GRAY[:3] + (60,), resolution=100)

    def update_animation(self, delta_time: float):
        self.trail.set_position(*self.position)
        self.dead_trail.set_position(*self.position)
        return super().update_animation(delta_time)

    def draw_trail(self):
        self.dead_trail.draw() if self.dead else self.trail.draw()

class FourKeyHighway(Highway):
    def __init__(self, chart: FourKeyChart, engine: FourKeyEngine, pos: tuple[int, int], size: tuple[int, int] = None, gap: int = 5, auto=False):
        if size is None:
            size = int(Settings.width / (1280 / 400)), Settings.height

        super().__init__(chart, pos, size, gap)
        self.engine = engine

        self.viewport = 0.5  # TODO: BPM scaling?

        self.auto = auto

        self.show_hit_window = False

        self.sprite_buckets = SpriteBucketCollection()
        for note in self.notes:
            sprite = FourKeyNoteSprite(note, self, self.note_size) if note.length == 0 else FourKeyLongNoteSprite(note, self, self.note_size)
            sprite.top = self.note_y(note.time)
            sprite.left = self.lane_x(note.lane)
            note.sprite = sprite
            self.sprite_buckets.append(sprite, note.time, note.length)
        logger.debug(f"Sustains: {len([s for s in self.sprite_buckets.sprites if isinstance(s, FourKeyLongNoteSprite)])}")

        self.strikeline = arcade.SpriteList()
        for i in [0, 1, 2, 3]:
            sprite = FourKeyNoteSprite(FourKeyNote(self.chart, 0, i, 0), self, self.note_size)
            sprite.top = self.strikeline_y
            sprite.left = self.lane_x(sprite.note.lane)
            sprite.alpha = 64
            self.strikeline.append(sprite)

        self.hit_window_mid = self.note_y(0) - (self.note_size / 2)
        self.hit_window_top = self.note_y(-0.075) - (self.note_size / 2)
        self.hit_window_bottom = self.note_y(0.075) - (self.note_size / 2)

        logger.debug(f"Generated highway for chart {chart.instrument}/{chart.difficulty}.")

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

    @property
    def pixel_offset(self):
        # TODO: Replace with better pixel_offset calculation
        return self._pixel_offset

    @property
    def pos(self) -> tuple[int, int]:
        return self._pos

    @pos.setter
    def pos(self, p: tuple[int, int]):
        old_pos = self._pos
        diff_x = p[0] - old_pos[0]
        diff_y = p[1] - old_pos[1]
        self._pos = p
        for bucket in self.sprite_buckets.buckets:
            bucket.move(diff_x, diff_y)
        self.sprite_buckets.overbucket.move(diff_x, diff_y)
        self.strikeline.move(diff_x, diff_y)

    def draw(self):
        _cam = arcade.get_window().current_camera
        self.camera.use()
        arcade.draw_lrtb_rectangle_filled(self.x, self.x + self.w,
                                          self.y + self.h, self.y,
                                          (0, 0, 0, 128))
        if self.show_hit_window:
            arcade.draw_lrtb_rectangle_filled(self.x, self.x + self.w,
                                              self.hit_window_top, self.hit_window_bottom,
                                              (255, 0, 0, 128))
        self.strikeline.draw()
        vp = arcade.get_viewport()
        height = vp[3] - vp[2]
        arcade.set_viewport(
            0,
            Settings.width,
            -self.pixel_offset,
            -self.pixel_offset + height
        )
        # Draw sustains.
        # TODO: This might be slow, don't loop over things.
        b = self.sprite_buckets.calc_bucket(self.song_time)
        window = arcade.get_window()
        for bucket in self.sprite_buckets.buckets[b:b+2] + [self.sprite_buckets.overbucket]:
            for note in bucket.sprite_list:
                if isinstance(note, FourKeyLongNoteSprite) and note.note.time < self.song_time + self.viewport:
                    # Clip the rendering to the strikeline if the key is being held.
                    if self.engine.key_state[note.note.lane] or self.auto:
                        window.ctx.scissor = (0, 0, window.width, self.hit_window_mid)
                    else:
                        window.ctx.scissor = None
                    note.draw_trail()
        window.ctx.scissor = None
        self.sprite_buckets.draw(self.song_time)
        _cam.use()

class FourKeyJudgement(Judgement):
    def get_texture(self) -> arcade.Texture:
        with pkg_resources.path(baseskin, f"judgement-{self.key}.png") as image_path:
            tex = arcade.load_texture(image_path, hit_box_algorithm = "None")
        return tex

class FourKeyEngine(Engine):
    def __init__(self, chart: FourKeyChart, offset: Seconds = -0.025):  # TODO: Set this dynamically
        hit_window: Seconds = 0.075
        fk = get_keymap().get_set("fourkey")
        mapping = [fk.key1, fk.key2, fk.key3, fk.key4]
        judgements = [
            #               ("name",           "key"             ms, score,  acc, hp=0)
            FourKeyJudgement("Super Charming", "supercharming",  10,  1000,    1, 0.04),
            FourKeyJudgement("Charming",       "charming",       25,  1000,  0.9, 0.04),
            FourKeyJudgement("Excellent",      "excellent",      35,   800,  0.8, 0.03),
            FourKeyJudgement("Great",          "great",          45,   600,  0.7, 0.02),
            FourKeyJudgement("Good",           "good",           60,   400,  0.6, 0.01),
            FourKeyJudgement("OK",             "ok",             75,   200,  0.5,    0),
            FourKeyJudgement("Miss",           "miss",     math.inf,     0,    0, -0.1)
        ]
        super().__init__(chart, mapping, hit_window, judgements, offset)

        self.min_hp = 0
        self.hp = 1
        self.max_hp = 2
        self.bomb_hp = 0.5

        self.has_died = False

        self.latest_judgement = None
        self.latest_judgement_time = None
        self.all_judgements: list[tuple[Seconds, Seconds, Judgement]] = []

        self.current_notes: list[FourKeyNote] = self.chart.notes.copy()
        self.current_events: list[DigitalKeyEvent] = []

        self.last_p1_note = None
        self.last_note_missed = False
        self.streak = 0
        self.max_streak = 0

        self.active_sustains: list[FourKeyNote] = []
        self.last_sustain_tick = 0

    def process_keystate(self):
        last_state = self.key_state
        key_states = get_keymap().get_set("fourkey").state
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
        self.key_state = key_states

    @property
    def average_acc(self) -> float:
        j = [j[1] for j in self.all_judgements if j[1] is not math.inf]
        return mean(j) if j else 0

    def calculate_score(self):
        # Get all non-scored notes within the current window
        for note in [n for n in self.current_notes if n.time <= self.chart_time + self.hit_window]:
            # Get sustains in the window and add them to the active sustains list
            if note.is_sustain and note not in self.active_sustains:
                self.active_sustains.append(note)
            # Missed notes (current time is higher than max allowed time for note)
            if self.chart_time > note.time + self.hit_window:
                note.missed = True
                note.hit_time = math.inf  # how smart is this? :thinking:
                self.score_note(note)
                self.current_notes.remove(note)
            else:
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
                            logger.info("Note removal failed!")
                        self.current_events.remove(event)
                        break

        for sustain in self.active_sustains:
            if self.chart_time > sustain.end + self.hit_window:
                self.active_sustains.remove(sustain)

        # Check sustains
        self.score_sustains()

        # Make sure we can't go below min_hp or above max_hp
        self.hp = clamp(self.min_hp, self.hp, self.max_hp)
        if self.hp == self.min_hp:
            self.has_died = True

        self.last_score_check = self.chart_time

    def score_note(self, note: FourKeyNote):
        # Ignore notes we haven't done anything with yet
        if not (note.hit or note.missed):
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

        # Judge the player
        rt = note.hit_time - note.time if note.hit_time is not math.inf else math.inf
        self.latest_judgement = j
        self.latest_judgement_time = self.chart_time
        self.all_judgements.append((self.latest_judgement_time, rt, self.latest_judgement))

        # Animation and hit/miss tracking
        self.last_p1_note = note.lane
        if note.hit:
            self.hits += 1
            self.streak += 1
            self.max_streak = max(self.streak, self.max_streak)
            self.last_note_missed = False
        elif note.missed:
            self.misses += 1
            self.streak = 0
            self.last_note_missed = True

    def score_sustains(self):
        raise NotImplementedError

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
