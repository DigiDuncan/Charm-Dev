from __future__ import annotations

from importlib.resources import files
from dataclasses import dataclass
from enum import Enum
from functools import cache
from pathlib import Path
import logging
from typing import cast

import PIL
import arcade
from arcade import Sprite, SpriteList, Texture, color as colors

from charm.lib.charm import load_missing_texture
from charm.lib.gamemodes.osu import OsuHitCircle, OsuSlider, OsuSpinner, RawOsuChart
from charm.lib.generic.engine import Engine
from charm.lib.generic.highway import Highway
from charm.lib.generic.song import Chart, Metadata, Note, Song
from charm.lib.spritebucket import SpriteBucketCollection
from charm.lib.utils import clamp, img_from_path

import charm.data.images.skins as skins
from charm.objects.line_renderer import TaikoNoteTrail

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
    def __init__(self, song: 'Song', difficulty: str, hash: str | None) -> None:
        super().__init__(song, "taiko", difficulty, "taiko", 1, hash)
        self.song: TaikoSong = song


class TaikoSong(Song[TaikoChart]):
    def __init__(self, path: Path):
        super().__init__(path)

    @classmethod
    def parse(cls, path: Path) -> TaikoSong:
        song = TaikoSong(path)

        chart_files = path.glob("*.osu")

        added_bpm_events = False

        for p in chart_files:
            raw_chart = RawOsuChart.parse(p)  # SO MUCH is hidden by this function
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
        # TODO: Handle no charts
        return song

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
        image = img_from_path(files(skins) / "taiko" / f"{image_name}.png")
        if image.height != height:
            width = int((height / image.height) * image.width)
            image = image.resize((width, height), PIL.Image.LANCZOS)
    except Exception as e:
        logger.error(f"Unable to load texture: {image_name} | {e}")
        return load_missing_texture(height, height)
    return Texture(image)


class TaikoNoteSprite(Sprite):
    def __init__(self, note: TaikoNote, highway: "TaikoHighway", height = 128, *args, **kwargs) -> None:
        self.note: TaikoNote = note
        self.highway: TaikoHighway = highway
        tex = load_note_texture(note.type.value, height)
        super().__init__(tex, *args, **kwargs)

    def update_animation(self, delta_time: float = 1 / 60) -> None:
        if self.note.type == NoteType.DENDEN:
            self.angle += 360 * delta_time / 3
        super().update_animation(delta_time)


class TaikoLongNoteSprite(TaikoNoteSprite):
    def __init__(self, note: TaikoNote, highway: "TaikoHighway", height = 128, *args, **kwargs) -> None:
        super().__init__(note, highway, *args, **kwargs)

        color = colors.YELLOW if note.type == NoteType.DRUMROLL else colors.MAGENTA
        self.trail = TaikoNoteTrail(self.position, self.note.length, self.highway.note_size, self.highway.px_per_s,
                                    color, color[:3] + (60,))

    def update_animation(self, delta_time: float):
        self.trail.set_position(*self.position)
        super().update_animation(delta_time)

    def draw_trail(self):
        self.trail.draw()


class TaikoHighway(Highway):
    def __init__(self, chart: Chart, pos: tuple[int, int], size: tuple[int, int] = None, gap: int = 5, auto = False):
        if size is None:
            self.window = arcade.get_window()
            size = int(self.window.width / (1280 / 400)), self.window.height

        super().__init__(chart, pos, size, gap)

        self.chart: TaikoChart = self.chart

        self.viewport = 0.75 * (1280 / 720)  # TODO: Set dynamically.

        self.auto = auto

        self.color = (0, 0, 0, 128)  # TODO: eventually this will be a scrolling image.

        self.note_sprites: list[TaikoNoteSprite] = []
        self.sprite_buckets = SpriteBucketCollection()
        for note in self.notes:
            note = cast("TaikoNote", note)
            sprite = TaikoNoteSprite(note, self, self.note_size) if note.length == 0 else TaikoLongNoteSprite(note, self, self.note_size)
            sprite.center_x = -self.note_y(note.time)
            sprite.center_y = self.y + (self.h / 2)
            if note.large:
                sprite.scale = 1.5
            note.sprite = sprite
            self.sprite_buckets.append(sprite, note.time, note.length)
            self.note_sprites.append(sprite)

        self.strikeline = SpriteList()

        for spritelist in self.sprite_buckets.buckets:
            spritelist.reverse()

        logger.debug(f"Generated highway for chart {chart.instrument}.")

        # TODO: Replace with better pixel_offset calculation
        self.last_update_time = 0
        self._pixel_offset = 0

        # USED FOR AUTO
        self.last_note_type = None
        self.last_note_big = False
        self.last_side_right = False
        self.frames_visible = 0

    @property
    def strikeline_y(self):
        return self.w / 10

    @property
    def note_size(self) -> int:
        return (self.h // self.chart.lanes)

    @property
    def px_per_s(self):
        return self.w / self.viewport

    def note_y(self, at: float):
        rt = at - self.song_time
        return (-self.px_per_s * rt) - self.strikeline_y + self.x

    def update(self, song_time: float):
        super().update(song_time)
        self.sprite_buckets.update_animation(song_time)
        # TODO: Replace with better pixel_offset calculation
        delta_draw_time = self.song_time - self.last_update_time
        self._pixel_offset -= (self.px_per_s * delta_draw_time)
        self.last_update_time = self.song_time

        self.highway_camera.position = (self.window.center_x-self.pixel_offset, self.window.center_y)

        if self.auto:
            # This feels gross, but I don't know how else to do it.
            b = clamp(0, self.sprite_buckets.calc_bucket(self.song_time), len(self.sprite_buckets.buckets) - 1)
            for bucket in [self.sprite_buckets.buckets[b]] + [self.sprite_buckets.overbucket]:
                for note_sprite in bucket.sprite_list:
                    if self.song_time > note_sprite.note.time and note_sprite.alpha != 0:
                        note_sprite.alpha = 0
                        self.last_note_type = note_sprite.note.type
                        self.last_note_big = note_sprite.note.large
                        self.last_side_right = not self.last_side_right
                        self.frames_visible = 0

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
        with self.static_camera.activate():
            arcade.draw_lrbt_rectangle_filled(self.x, self.x + self.w,
                                              self.y, self.y + self.h,
                                              self.color)
            arcade.draw_circle_filled(self.strikeline_y, self.y + (self.h / 2), self.note_size, self.color)

            if self.auto and self.last_note_type and self.frames_visible <= 6:
                # The 6 there is really hardcoded and this function is probably very slow because it does a ton of arcade.draw* calls
                if self.last_note_type == NoteType.DON:
                    if self.last_note_big:
                        arcade.draw_circle_filled(self.strikeline_y, self.y + (self.h / 2), self.note_size * 0.75, colors.DEBIAN_RED)
                    elif self.last_side_right:
                        arcade.draw_arc_filled(self.strikeline_y, self.y + (self.h / 2), self.note_size * 2 * 0.75, self.note_size * 2 * 0.75, colors.DEBIAN_RED, -90, 90)
                    else:
                        arcade.draw_arc_filled(self.strikeline_y, self.y + (self.h / 2), self.note_size * 2 * 0.75, self.note_size * 2 * 0.75, colors.DEBIAN_RED, 90, 270)
                elif self.last_note_type == NoteType.KAT:
                    if self.last_note_big:
                        arcade.draw_circle_outline(self.strikeline_y, self.y + (self.h / 2), self.note_size, colors.BRIGHT_CERULEAN, 10)
                    elif self.last_side_right:
                        arcade.draw_arc_outline(self.strikeline_y, self.y + (self.h / 2), self.note_size * 2, self.note_size * 2, colors.BRIGHT_CERULEAN, -90, 90, 20)
                    else:
                        arcade.draw_arc_outline(self.strikeline_y, self.y + (self.h / 2), self.note_size * 2, self.note_size * 2, colors.BRIGHT_CERULEAN, 90, 270, 20)
                self.frames_visible += 1

            self.strikeline.draw()

            self.highway_camera.use()
            b = self.sprite_buckets.calc_bucket(self.song_time)
            for bucket in self.sprite_buckets.buckets[b:b + 2] + [self.sprite_buckets.overbucket]:
                for note in bucket.sprite_list:
                    if isinstance(note, TaikoLongNoteSprite) and note.note.time < self.song_time + self.viewport and note.note.end > self.song_time:
                        note.draw_trail()
            self.sprite_buckets.draw(self.song_time)
