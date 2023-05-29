from dataclasses import dataclass
from enum import Enum
from functools import cache
from pathlib import Path
import logging

import PIL
import arcade
from arcade import Sprite

from charm.lib.charm import load_missing_texture
from charm.lib.gamemodes.osu import OsuHitCircle, OsuSlider, OsuSpinner, RawOsuChart
from charm.lib.generic.engine import Engine
from charm.lib.generic.highway import Highway
from charm.lib.generic.song import Chart, Metadata, Note, Song
from charm.lib.spritebucket import SpriteBucketCollection
from charm.lib.utils import img_from_resource

import charm.data.images.skins.taiko as taikoskin

logger = logging.getLogger("charm")

class NoteType(Enum):
    DON = "don"
    KAT = "kat"
    DRUMROLL = "drumroll"
    DENDEN = "denden"

@dataclass
class TaikoNote(Note):
    large: bool = False

class TaikoChart(Chart):
    def __init__(self, song: 'Song', difficulty: str, hash: str) -> None:
        super().__init__(song, "taiko", difficulty, "taiko", 4, hash)
        self.song: TaikoSong = song

class TaikoSong(Song):
    def __init__(self, path: Path):
        super().__init__(path)

    @classmethod
    def parse(self, folder: Path) -> "TaikoSong":
        song = TaikoSong(folder)

        chart_files = folder.glob("*.osu")

        added_bpm_events = False

        for p in chart_files:
            raw_chart = RawOsuChart.parse(p)
            chart = TaikoChart(song, raw_chart.metadata.difficulty, None)
            if not added_bpm_events:
                song.events.extend(raw_chart.timing_points)
                added_bpm_events = True
            for hit_object in raw_chart.hit_objects:
                if isinstance(hit_object, OsuHitCircle):
                    if hit_object.taiko_kat:
                        chart.notes.append(TaikoNote(chart, hit_object.time, 0, 0, NoteType.KAT, large = hit_object.taiko_large))
                    else:
                        chart.notes.append(TaikoNote(chart, hit_object.time, 0, 0, NoteType.DON, large = hit_object.taiko_large))
                elif isinstance(hit_object, OsuSlider):
                    chart.notes.append(TaikoNote(chart, hit_object.time, 0, hit_object.length, NoteType.DRUMROLL, large = hit_object.taiko_large))
                elif isinstance(hit_object, OsuSpinner):
                    chart.notes.append(TaikoNote(chart, hit_object.time, 0, hit_object.length, NoteType.DENDEN, large = hit_object.taiko_large))
            song.charts.append(chart)

    @classmethod
    def get_metadata(self, folder: Path) -> Metadata:
        chart_files = folder.glob("*.osu")
        raw_chart = RawOsuChart.parse(next(chart_files))
        m = raw_chart.metadata
        return Metadata(
            m.title,
            m.artist,
            m.source,
            charter = m.charter,
            path = folder,
            gamemode = "taiko"
        )

class TaikoEngine(Engine):
    pass

@cache
def load_note_texture(note_type: str, height: int):
    image_name = f"{note_type}"
    try:
        image = img_from_resource(taikoskin, image_name + ".png")
        if image.height != height:
            width = int((height / image.height) * image.width)
            image = image.resize((width, height), PIL.Image.LANCZOS)
    except Exception as e:
        logger.error(f"Unable to load texture: {image_name} | {e}")
        return load_missing_texture(height, height)
    return arcade.Texture(image)

class TaikoNoteSprite(Sprite):
    def __init__(self, note: TaikoNote, highway: "TaikoHighway", height = 128, *args, **kwargs) -> None:
        self.note: TaikoNote = note
        self.highway: TaikoHighway = highway
        tex = load_note_texture(note.type, height)
        super().__init__(tex, *args, **kwargs)

class TaikoHighway(Highway):
    def __init__(self, chart: Chart, pos: tuple[int, int], size: tuple[int, int] = None, gap: int = 5, auto = False):
        if size is None:
            self.window = arcade.get_window()
            size = int(self.window.width / (1280 / 400)), self.window.height

        super().__init__(chart, pos, size, gap)

        self.chart: TaikoChart = self.chart

        self.viewport = 0.75  # TODO: Set dynamically.

        self.auto = auto

        self.color = (0, 0, 0, 128)  # TODO: eventually this will be a scrolling image.

        self.note_sprites: list[TaikoNoteSprite] = []
        self.sprite_buckets = SpriteBucketCollection()
        for note in self.notes:
            sprite = TaikoNoteSprite(note, self, self.note_size)
            sprite.top = self.note_y(note.time)
            sprite.center = self.x + (self.w / 2)
            note.sprite = sprite
            self.sprite_buckets.append(sprite, note.time, note.length)
            self.note_sprites.append(sprite)

        self.strikeline = arcade.SpriteList()

        for spritelist in self.sprite_buckets.buckets:
            spritelist.reverse()

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

        self.highway_camera.move((0.0, self.pixel_offset))
        self.highway_camera.update()

        if self.auto:
            i = self.chart.indexes_by_time["note"].lteq_index(self.song_time - 0.050) or 0
            while True:
                note_sprite = self.note_sprites[i]
                if note_sprite.note.time > self.song_time + 0.065:
                    break
                if self.song_time > note_sprite.note.time:
                    note_sprite.alpha = 0
                i += 1

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

    @property
    def pixel_offset(self):
        # TODO: Replace with better pixel_offset calculation
        return self._pixel_offset

    def draw(self):
        _cam = arcade.get_window().current_camera
        self.static_camera.use()
        arcade.draw_lrtb_rectangle_filled(self.x, self.x + self.w,
                                          self.y + self.h, self.y,
                                          self.color)
        self.strikeline.draw()

        self.highway_camera.use()
        self.sprite_buckets.draw(self.song_time)
        _cam.use()
