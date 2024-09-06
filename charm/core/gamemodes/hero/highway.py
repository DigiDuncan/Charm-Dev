import math
from typing import Any
from collections.abc import Generator
from functools import cache
from importlib.resources import files
import logging
import PIL.Image

from arcade import SpriteList, Sprite, Texture, draw_line, draw_rect_filled, LRBT
import arcade.color as colors
from arcade.camera import PerspectiveProjector
from arcade.camera.grips import rotate_around_right

from charm.lib.charm import load_missing_texture
from charm.lib.utils import img_from_path
from charm.lib.pool import Pool, SpritePool
from charm.core.generic.chart import Chart
from charm.core.generic.engine import Engine
from charm.core.generic.highway import Highway
from charm.core.generic.sprite import NoteSprite, StrikelineSprite, SustainSprites, SustainTextureDict, SustainTextures, get_note_color_by_beat
from charm.core.gamemodes.hero.chart import HeroChart, HeroNote, BeatEvent

import charm.data.images.skins as skins

logger = logging.getLogger("charm")

# SKIN
@cache
def load_note_texture(note_type: str, note_lane: int, height: int) -> Texture:
    image_name = f"{note_type}-{note_lane + 1}"
    open_height = int(height / (128 / 48))
    try:
        image = img_from_path(files(skins) / "hero" / f"{image_name}.png")
        if image.height != height and note_lane != 7:
            width = int((height / image.height) * image.width)
            image = image.resize((width, height), PIL.Image.LANCZOS)
        elif image.height != open_height:
            width = int((open_height / image.height) * image.width)
            image = image.resize((width, open_height), PIL.Image.LANCZOS)
    except Exception as e:  # noqa: BLE001
        logger.error(f"Unable to load texture: {image_name} | {e}")
        return load_missing_texture(height, height)
    return Texture(image)


HERO_HIGHWAY_ANGLE = 70.0
HERO_HIGHWAY_DIST = 400.0
HERO_LANE_COUNT = 5

class HeroHighway(Highway):

    def __init__(self, chart: Chart, engine: Engine, pos: tuple[int, int], size: tuple[int, int] = None, gap: int = 5, *, show_flags: bool = False):
        static_camera = PerspectiveProjector()
        highway_camera = PerspectiveProjector(projection=static_camera.projection)

        self.chart: HeroChart
        super().__init__(chart, engine, pos, size, gap, downscroll=True, static_camera=static_camera, highway_camera=highway_camera)

        # Using some triginomerty we find the angle and position of the perspective camera's
        # to give us the classic hero look
        data_h_fov = 0.5 * static_camera.projection.fov
        static_camera.projection.far = 10000.0
        look_radians = math.radians(HERO_HIGHWAY_ANGLE - data_h_fov)

        self.perp_y_pos = -HERO_HIGHWAY_DIST * math.sin(look_radians)
        self.perp_z_pos = HERO_HIGHWAY_DIST * math.cos(look_radians)

        static_data = static_camera.view
        highway_data = highway_camera.view

        static_data.position = highway_data.position = (self.window.center_x, self.perp_y_pos, self.perp_z_pos)
        static_data.up, static_data.forward = highway_data.up, highway_data.forward = rotate_around_right(static_data, -HERO_HIGHWAY_ANGLE)

        # NOTE POOL DEFINITION AND CONSTRUCTION

        # Generators are great for ease, but it means we can't really 'scrub' backwards through the song
        # So this is a patch job at best.
        self._note_generator: Generator[HeroNote, Any, None] = (note for note in self.notes)

        self._note_pool: SpritePool[NoteSprite] = SpritePool([NoteSprite(x=-1000.0, y=-1000.0) for _ in range(1000)])
        # avoid orthographic culling TODO: make source program more accessable
        self._note_pool._source.program = self.window.ctx.sprite_list_program_no_cull # noqa: SLF001

        self._next_note: HeroNote = next(self._note_generator, None)

        # SUSTAIN POOL DEFINITION AND CONSTRUCTION

        # Generators are great for ease, but it means we can't really 'scrub' backwards through the song
        # So this is a patch job at best.
        self._sustain_generator: Generator[HeroNote, Any, None] = (note for note in self.notes if note.length)

        self._sustain_pool: Pool[SustainSprites] = Pool([SustainSprites(self.note_size, self.note_size/2.0, downscroll=True) for _ in range(100)])
        self._sustain_sprites: SpriteList[Sprite] = SpriteList()
        self._sustain_sprites.program = self.window.ctx.sprite_list_program_no_cull  # avoid orthographic culling
        for sustain in self._sustain_pool.source:
            self._sustain_sprites.extend(sustain.get_sprites())

        # TODO: Add lane 7 (open) sustains correctly
        _missed_tail = load_note_texture('tail', 5, self.note_size)
        _missed_body = load_note_texture('body', 5, self.note_size)
        _missed_cap = load_note_texture('cap', 5, self.note_size // 2)

        self._sustain_textures: dict[int, SustainTextureDict] = {
            i: {'primary': SustainTextures(
                    load_note_texture('tail', i, self.note_size),
                    load_note_texture('body', i, self.note_size),
                    load_note_texture('cap', i, self.note_size // 2)
                ),
                'miss': SustainTextures(_missed_tail, _missed_body, _missed_cap)}
        for i in range(6)}

        self._next_sustain: HeroNote = next(self._sustain_generator, None)

        self._show_flags = show_flags

        self.color = (0, 0, 0, 128)  # TODO: eventually this will be a scrolling image.

        self.strikeline: SpriteList[StrikelineSprite] = SpriteList()
        self.strikeline.program = self.strikeline.ctx.sprite_list_program_no_cull
        y = self.strikeline_y - self.note_size/2.0
        for lane in range(5):
            x = self.lane_x(lane) + self.note_size/2.0
            sprite = StrikelineSprite(
                x, y,
                active_texture=load_note_texture("normal", lane, self.note_size),
                inactive_texture=load_note_texture("strikeline", lane, self.note_size),
                inactive_alpha=128
            )
            self.strikeline.append(sprite)

        logger.debug(f"Generated highway for chart {chart.metadata.instrument}.")

        # TODO: Replace with better pixel_offset calculation or remove entirely
        self.last_update_time = 0
        self._pixel_offset = 0

    def update(self, song_time: float) -> None:
        super().update(song_time)

        while self._next_note is not None and self._next_note.time <= (self.song_time + self.viewport) and self._note_pool.has_free_slot():
            note = self._next_note
            sprite = self._note_pool.get()
            sprite.texture = load_note_texture(note.type, note.lane, self.note_size)
            sprite.position = self.lane_x(note.lane) + sprite.width/2, self.note_y(note.time) - sprite.height/2.0
            sprite.visible = True
            sprite.note = note

            self._next_note = next(self._note_generator, None)
            # Filters out the flags if they aren't supposed to be shown
            while self._next_note and (self._next_note.lane in {5, 6}) and not self._show_flags:
                self._next_note = next(self._note_generator, None)

        while self._next_sustain is not None and self._next_sustain.time <= (self.song_time + self.viewport) and self._sustain_pool.has_free_slot():
            note = self._next_sustain
            sustain = self._sustain_pool.get()
            sustain.place(
                note,
                self.lane_x(self._next_sustain.lane) + sustain.size/2.0,
                self.note_y(note.time) - sustain.size/2.0,
                note.length * self.px_per_s,
                self._sustain_textures[note.lane]
            )

            self._next_sustain = next(self._sustain_generator, None)

        for sprite in self._note_pool.given_items:
            sprite.center_y = self.note_y(sprite.note.time) - sprite.height/2.0
            if sprite.note.hit or sprite.note.time <= (song_time - 0.1):
                sprite.visible = False
                self._note_pool.give(sprite)

        for sustain in self._sustain_pool.given_items:
            sustain.update_texture()
            sustain.update_sustain(self.note_y(sustain.note.time) - sustain.size/2.0, sustain.note.length * self.px_per_s)
            if sustain.note.end <= (song_time - 0.1):
                sustain.hide()
                self._sustain_pool.give(sustain)

    def draw(self) -> None:
        self.window.ctx.blend_func = self.window.ctx.BLEND_DEFAULT
        with self.static_camera.activate():
            draw_rect_filled(
                LRBT(self.x, self.x + self.w, self.y, self.y + self.h),
                self.color
            )
            current_beat_idx = self.chart.indices.beat_time.lteq_index(self.song_time)
            last_beat_idx = self.chart.indices.beat_time.lteq_index(self.song_time + self.viewport)
            if current_beat_idx is not None and last_beat_idx is not None:
                for beat in self.chart.events_by_type(BeatEvent)[current_beat_idx:last_beat_idx + 1]:
                    px = self.note_y(beat.time) - (self.note_size / 2)
                    draw_line(self.x, px, self.x + self.w, px, colors.DARK_GRAY, 3 if beat.major else 1)

            self.strikeline.draw()

            self._sustain_sprites.draw()
            self._note_pool.draw()

    def lane_x(self, lane_num: int) -> int:
        if lane_num == 7:  # tap note override
            return self.x
        return (self.note_size + self.gap) * lane_num + self.x

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

    @property
    def note_size(self) -> int:
        return int((self.w // HERO_LANE_COUNT) - self.gap)
