from __future__ import annotations

from importlib.resources import files, as_file
import logging
import math
from functools import cache
from statistics import mean
from typing import Literal, cast, Any

import arcade
from arcade import SpriteList, Texture, color as colors
from arcade.types import Color
import PIL
import PIL.ImageFilter
import PIL.ImageOps
import PIL.ImageEnhance

import charm.data.images.skins as skins
from charm.lib.charm import load_missing_texture
from charm.lib.generic.engine import DigitalKeyEvent, Engine, AutoEngine, Judgement
from charm.lib.generic.highway import Highway
from charm.lib.generic.results import Results
from charm.lib.generic.song import Note, Chart, Seconds, Song
from charm.lib.generic.sprite import NoteSprite, SustainSprites, StrikelineSprite, SustainTextureDict, SustainTextures
from charm.lib.keymap import keymap, Action
from charm.lib.utils import img_from_path, clamp
from charm.lib.pool import Pool, OrderedPool

logger = logging.getLogger("charm")


class NoteType:
    NORMAL = "normal"
    BOMB = "bomb"
    DEATH = "death"
    HEAL = "heal"
    CAUTION = "caution"
    STRIKELINE = "strikeline"


# SKIN
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
    def from_note(cls, note: FourKeyNote) -> Color:
        if note.type == NoteType.NORMAL:
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
        if note.type == NoteType.BOMB:
            return cls.BOMB
        elif note.type == NoteType.DEATH:
            return cls.DEATH
        elif note.type == NoteType.HEAL:
            return cls.HEAL
        elif note.type == NoteType.CAUTION:
            return cls.CAUTION
        else:
            return colors.BLACK


# SKIN
def get_note_color_by_beat(beat: int) -> tuple[int, int, int]:
    beat_color = {
        1: (0xFF, 0x00, 0x00),
        2: (0x00, 0x00, 0xFF),
        3: (0x00, 0xFF, 0x00),
        4: (0xFF, 0xFF, 0x00),
        5: (0xAA, 0xAA, 0xAA),
        6: (0xFF, 0x00, 0xFF),
        8: (0xFF, 0x77, 0x00),
        12: (0x00, 0xFF, 0xFF),
        16: (0x00, 0x77, 0x00),
        24: (0xCC, 0xCC, 0xCC),
        32: (0xAA, 0xAA, 0xFF),
        48: (0x55, 0x77, 0x55)
    }
    default_color = (0x00, 0x22, 0x22)
    return beat_color.get(beat, default_color)


# SKIN
@cache
def load_note_texture(note_type: str, note_lane: int, height: int, value: int = 0, *, fnf: bool = False) -> Texture:
    if value and note_type == NoteType.NORMAL:
        # "Beat colors", which color a note based on where it lands in the beat.
        # This is useful for desnely packed patterns, and some rhythm games rely
        # on it for readability.
        image_name = f"gray-{note_lane + 1}"
        try:
            image = img_from_path(files(skins) / "fourkey" / f"{image_name}.png")
            if image.height != height:
                width = int((height / image.height) * image.width)
                image = image.resize((width, height), PIL.Image.LANCZOS)
        except Exception:  # noqa: BLE001
            logger.error(f"Unable to load texture: {image_name}")
            return load_missing_texture(height, height)
        color = get_note_color_by_beat(value)
        r, g, b, a = image.split()
        image = image.convert("L")
        image = PIL.ImageOps.colorize(image, (0, 0, 0), (255, 255, 255), color)
        image = image.convert("RGBA")
        image.putalpha(a)
    else:
        image_name = f"{note_type}-{note_lane + 1}"
        try:
            if fnf:  # HACK: probably not a great way to do this!
                image = img_from_path(files(skins) / "fnf" / f"{image_name}.png")
            else:
                image = img_from_path(files(skins) / "fourkey" / f"{image_name}.png")
            if image.height != height:
                width = int((height / image.height) * image.width)
                image = image.resize((width, height), PIL.Image.LANCZOS)
        except Exception:  # noqa: BLE001
            logger.error(f"Unable to load texture: {image_name}")
            return load_missing_texture(height, height)
    return Texture(image)


class FourKeyNote(Note):
    def __init__(self, chart: Chart, time: Seconds, lane: Literal[0,1,2,3],
                 length: Seconds = 0, type: str = "normal", value: int = 0,
                 hit: bool = False, missed: bool = False,
                 hit_time: Seconds | None = None,
                 extra_data: tuple[Any, ...] | None = None,
                 parent: FourKeyNote | None = None):
        super().__init__(chart, time, lane, length, type, value, hit, missed, hit_time, extra_data)
        self.parent = parent
        self.lane: Literal[0,1,2,3]

    def __lt__(self, other: FourKeyNote):
        return (self.time, self.lane, self.type) < (other.time, other.lane, other.type)


class FourKeyChart(Chart):
    def __init__(self, song: Song, difficulty: str, hash: str | None):
        super().__init__(song, "4k", difficulty, "4k", 4, hash)
        self.song: FourKeySong = song


class FourKeySong(Song[FourKeyChart]):
    pass


class FourKeyHighway(Highway):
    def __init__(self, chart: FourKeyChart, engine: FourKeyEngine | AutoEngine, pos: tuple[int, int], size: tuple[int, int] = None, gap: int = 5):
        if size is None:
            self.window = arcade.get_window()
            size = int(self.window.width / (1280 / 400)), self.window.height

        super().__init__(chart, pos, size, gap)
        self.engine = engine

        # TODO: re-add the functionality of
        self.viewport = 0.75  # TODO: BPM scaling?

        # NOTE POOL DEFINITION AND CONSTRUCTION

        # Generators are great for ease, but it means we can't really 'scrub' backwards through the song
        # So this is a patch job at best.
        self._note_generator = (note for note in self.notes if note.type != 'sustain')

        self._note_sprites = SpriteList(capacity=1024)
        self._note_sprites.extend([NoteSprite(x=-1000.0, y=-1000.0) for _ in range(1000)])
        self._note_pool: OrderedPool[NoteSprite] = OrderedPool(self._note_sprites)  # type: ignore[]
        self._note_sprites = SpriteList(capacity=1024)
        self._note_sprites.extend(self._note_pool.source)

        self._note_textures = {
            t: {l: load_note_texture(t, l, self.note_size) for l in range(4)} for t in (NoteType.NORMAL, NoteType.BOMB, NoteType.DEATH, NoteType.HEAL, NoteType.CAUTION)
        }

        self._next_note = next(self._note_generator, None)

        # SUSTAIN POOL DEFINITION AND CONSTRUCTION

        # Generators are great for ease, but it means we can't really 'scrub' backwards through the song
        # So this is a patch job at best.
        self._sustain_generator = (note for note in self.notes if note.length)

        self._sustain_pool: Pool[SustainSprites] = Pool([SustainSprites(self.note_size) for _ in range(100)])
        self._sustain_sprites = SpriteList(capacity=512)
        for sustain in self._sustain_pool.source:
            self._sustain_sprites.extend(sustain.get_sprites())

        self._sustain_textures: dict[int, SustainTextureDict] = {
            i: {'primary': SustainTextures(load_note_texture('tail', i, self.note_size), load_note_texture('body', i, self.note_size), load_note_texture('cap', i, self.note_size // 2))}
        for i in range(4)}

        self._next_sustain = next(self._sustain_generator, None)

        self.bg_color: Color = Color(0, 0, 0, 128)  # SKIN
        self.show_hit_window = False

        self.strikeline: SpriteList[StrikelineSprite] = SpriteList(capacity=4)
        y = self.strikeline_y - self.note_size/2.0
        for lane in (0, 1, 2, 3):
            x = self.lane_x(lane) + self.note_size/2.0
            sprite = StrikelineSprite(
                x, y,
                active_texture=load_note_texture("normal", lane, self.note_size),
                inactive_texture=load_note_texture("strikeline", lane, self.note_size)
            )
            self.strikeline.append(sprite)

        self.hit_window_mid = self.note_y(0) - (self.note_size / 2)
        self.hit_window_top = self.note_y(-self.engine.hit_window) - (self.note_size / 2)
        self.hit_window_bottom = self.note_y(self.engine.hit_window) - (self.note_size / 2)

        logger.debug(f"Generated highway for chart {chart.instrument}/{chart.difficulty}.")

        # TODO: Replace with better pixel_offset calculation
        self.last_update_time = 0
        self._pixel_offset = 0
        self.keystate = keymap.fourkey.state

    def update(self, song_time: float) -> None:
        super().update(song_time)

        while self._next_note is not None and self._next_note.time <= (song_time + self.viewport) and self._note_pool.has_free_slot():
            sprite = self._note_pool.get()
            sprite.texture = self._note_textures[self._next_note.type][self._next_note.lane]
            sprite.note = self._next_note
            sprite.position = self.lane_x(self._next_note.lane) + sprite.width/2.0, self.note_y(sprite.note.time) - sprite.height/2.0
            sprite.visible = True

            self._next_note = next(self._note_generator, None)

        while self._next_sustain is not None and self._next_sustain.time <= (song_time + self.viewport) and self._sustain_pool.has_free_slot():
            sustain = self._sustain_pool.get()
            sustain.place(
                self._next_sustain,
                self.lane_x(self._next_sustain.lane) + sustain.size/2.0,
                self.strikeline_y - sustain.size/2.0,
                self._next_sustain.length * self.px_per_s,
                self._sustain_textures[self._next_sustain.lane]
            )

            self._next_sustain = next(self._sustain_generator, None)

        # for sprite in self._note_pool.given_items:
        #     # TODO note_y and lane_x need to work of center not top left
        #     sprite.center_y = self.note_y(sprite.note.time) - sprite.height/2.0
        #     sprite.center_x = self.lane_x(sprite.note.lane) + sprite.width/2.0

        #     if sprite.note.hit or sprite.note.end <= (song_time - 0.1):
        #         sprite.visible = False
        #         self._note_pool.give(sprite)

        # for sustain in self._sustain_pool.given_items:
        #     sustain.update_texture()
        #     sustain.update_sustain(self.note_y(sustain.note.time) - sustain.size/2.0, sustain.note.length * self.px_per_s)
        #     if sustain.note.end <= (song_time - 0.1):
        #         sustain.hide()
        #         self._sustain_pool.give(sustain)

        # TODO: Replace with better pixel_offset calculation
        delta_draw_time = self.song_time - self.last_update_time
        self._pixel_offset += (self.px_per_s * delta_draw_time)
        self.last_update_time = self.song_time

        self.update_strikeline()

    def update_strikeline(self) -> None:
        if self.keystate == self.engine.keystate:
            return
        self.keystate = self.engine.keystate
        for strikeline, active in zip(self.strikeline, self.keystate, strict=True):
            strikeline.active = active

    @property
    def pixel_offset(self) -> int:
        # TODO: Replace with better pixel_offset calculation
        return self._pixel_offset

    @property
    def pos(self) -> tuple[int, int]:
        return self._pos

    @pos.setter
    def pos(self, p: tuple[int, int]) -> None:
        old_pos = self._pos
        diff_x = p[0] - old_pos[0]
        diff_y = p[1] - old_pos[1]
        self._pos = p
        self.strikeline.move(diff_x, diff_y)
        self.hit_window_mid = self.note_y(0) - (self.note_size / 2)
        self.hit_window_top = self.note_y(-self.engine.hit_window) - (self.note_size / 2)
        self.hit_window_bottom = self.note_y(self.engine.hit_window) - (self.note_size / 2)

    def draw(self) -> None:
        _cam = arcade.get_window().current_camera
        with self.static_camera.activate():
            arcade.draw_lrbt_rectangle_filled(self.x, self.x + self.w,
                                              self.y, self.y + self.h,
                                              self.bg_color)
            if self.show_hit_window:
                arcade.draw_lrbt_rectangle_filled(self.x, self.x + self.w,
                                                  self.hit_window_bottom, self.hit_window_top,
                                                  (255, 0, 0, 128))
            self.strikeline.draw()

            for sprite in self._note_pool.given_items:
                # TODO note_y and lane_x need to work of center not top left
                sprite.center_y = self.note_y(sprite.note.time) - sprite.height/2.0
                sprite.center_x = self.lane_x(sprite.note.lane) + sprite.width/2.0

                if sprite.note.hit or sprite.note.end <= (self.song_time - 0.1):
                    sprite.position = -1000.0, -1000.0
                    sprite.visible = False
                    self._note_pool.give(sprite)

            for sustain in self._sustain_pool.given_items:
                sustain.update_texture()
                sustain.update_sustain(self.note_y(sustain.note.time) - sustain.size/2.0, sustain.note.length * self.px_per_s)
                if sustain.note.end <= (self.song_time - 0.1):
                    sustain.hide()
                    self._sustain_pool.give(sustain)

            self._sustain_sprites.draw(pixelated=True)
            self._note_sprites.draw(pixelated=True)
        _cam.use()


# SKIN
class FourKeyJudgement(Judgement):
    def get_texture(self) -> Texture:
        with as_file(files(skins) / "base" / f"judgement-{self.key}.png") as p:
            tex = arcade.load_texture(p)
        return tex


class FourKeyEngine(Engine):
    def __init__(self, chart: FourKeyChart, offset: Seconds = 0):  # TODO: Set this dynamically
        hit_window: Seconds = 0.075
        judgements = [
            #               ("name",           "key"             ms, score, acc, hp=0)
            FourKeyJudgement("Super Charming", "supercharming",  10, 1000, 1.0, 0.04),
            FourKeyJudgement("Charming",       "charming",       25, 1000, 0.9, 0.04),
            FourKeyJudgement("Excellent",      "excellent",      35, 800,  0.8, 0.03),
            FourKeyJudgement("Great",          "great",          45, 600,  0.7, 0.02),
            FourKeyJudgement("Good",           "good",           60, 400,  0.6, 0.01),
            FourKeyJudgement("OK",             "ok",             75, 200,  0.5),
            FourKeyJudgement("Miss",           "miss",     math.inf,   0,    0, -0.1)
        ]
        super().__init__(chart, hit_window, judgements, offset)

        self.min_hp = 0
        self.hp = 1
        self.max_hp = 2
        self.bomb_hp = 0.5

        self.has_died = False

        self.latest_judgement = None
        self.latest_judgement_time = None
        self.all_judgements: list[tuple[Seconds, Seconds, Judgement]] = []

        self.current_notes: list[FourKeyNote] = self.chart.notes.copy()
        self.current_events: list[DigitalKeyEvent[Literal[0, 1, 2, 3]]] = []

        self.last_p1_action: Action | None = None
        self.last_note_missed = False
        self.streak = 0
        self.max_streak = 0

        self.active_sustains: list[FourKeyNote] = []
        self.last_sustain_tick = 0
        self.keystate: tuple[bool, bool, bool, bool] = (False, False, False, False)

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        self.keystate = keymap.fourkey.state
        # ignore spam during front/back porch
        if (self.chart_time < self.chart.notes[0].time - self.hit_window \
           or self.chart_time > self.chart.notes[-1].time + self.hit_window):
            return
        action = keymap.fourkey.pressed_action
        if action is None:
            return
        key = cast(Literal[0, 1, 2, 3], keymap.fourkey.actions.index(action))
        self.current_events.append(DigitalKeyEvent(self.chart_time, key, "down"))

    def on_key_release(self, symbol: int, modifiers: int) -> None:
        self.keystate = keymap.fourkey.state
        if self.last_p1_action is not None and not self.last_p1_action.held:
            self.last_p1_action = None
        # ignore spam during front/back porch
        if (self.chart_time < self.chart.notes[0].time - self.hit_window \
           or self.chart_time > self.chart.notes[-1].time + self.hit_window):
            return
        action = keymap.fourkey.released_action
        if action is None:
            return
        key = cast(Literal[0,1,2,3], keymap.fourkey.actions.index(action))
        self.current_events.append(DigitalKeyEvent(self.chart_time, key, "up"))

    @property
    def average_acc(self) -> float:
        j = [j[1] for j in self.all_judgements if j[1] is not math.inf]
        return mean(j) if j else 0

    def calculate_score(self) -> None:
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

    def score_note(self, note: FourKeyNote) -> None:
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
        rt = note.hit_time - note.time
        self.latest_judgement = j
        self.latest_judgement_time = self.chart_time
        self.all_judgements.append((self.latest_judgement_time, rt, self.latest_judgement))

        # Animation and hit/miss tracking
        self.last_p1_action = keymap.fourkey.actions[note.lane]
        if note.hit:
            self.hits += 1
            self.streak += 1
            self.max_streak = max(self.streak, self.max_streak)
            self.last_note_missed = False
        elif note.missed:
            self.misses += 1
            self.streak = 0
            self.last_note_missed = True

    def score_sustains(self) -> None:
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
