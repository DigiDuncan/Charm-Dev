from functools import cache
from importlib.resources import files
import logging

import PIL.Image
import PIL.ImageOps
import arcade
from arcade import SpriteList, Texture
from arcade.types import Color

import charm.data.images.skins as skins
from charm.core.charm import load_missing_texture
from charm.lib.pool import Pool, SpritePool
from charm.lib.utils import img_from_path

from charm.game.generic import Highway
from charm.game.generic.sprite import NoteSprite, StrikelineSprite, SustainSprites, SustainTextureDict, SustainTextures, get_note_color_by_beat
from .chart import FourKeyChart, FourKeyNote, FourKeyNoteType
from .engine import FourKeyEngine

logger = logging.getLogger("charm")


@cache
def load_note_texture(note_type: str, note_lane: int, height: int, value: int = 0, *, fnf: bool = False) -> Texture:
    if value and note_type == FourKeyNoteType.NORMAL:
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


class FourKeyHighway(Highway[FourKeyChart, FourKeyNote, FourKeyEngine]):
    def __init__(self, chart: FourKeyChart, engine: FourKeyEngine, pos: tuple[int, int], size: tuple[int, int] | None = None, gap: int = 5):
        super().__init__(chart, engine, pos, size, gap)

        # TODO: re-add the functionality of
        self.viewport = 0.75  # TODO: BPM scaling?

        # NOTE POOL DEFINITION AND CONSTRUCTION

        # Generators are great for ease, but it means we can't really 'scrub' backwards through the song
        # So this is a patch job at best.
        self._note_generator = (note for note in self.notes if note.type != 'sustain')
        self._note_pool: SpritePool[NoteSprite] = SpritePool([NoteSprite(x=-1000.0, y=-1000.0) for _ in range(1000)])
        # self._note_sprites = SpriteList(capacity=1024)
        # self._note_sprites.extend(self._note_pool.source)

        self._note_textures = {
            t: {l: load_note_texture(t, l, self.note_size) for l in range(4)} for t in (FourKeyNoteType.NORMAL, FourKeyNoteType.BOMB, FourKeyNoteType.DEATH, FourKeyNoteType.HEAL, FourKeyNoteType.CAUTION)
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

        logger.debug(f"Generated highway for chart {chart.metadata.instrument}/{chart.metadata.difficulty}.")

        self.keystate = (False, False, False, False)

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

        self.update_strikeline()

    def update_strikeline(self) -> None:
        if self.keystate == self.engine.keystate:
            return
        self.keystate = self.engine.keystate
        for strikeline, active in zip(self.strikeline, self.keystate, strict=True):
            strikeline.active = active

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

    @property
    def note_size(self) -> int:
        return (self.w // 4) - self.gap

    def draw(self) -> None:
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

            self._sustain_sprites.draw()
            self._note_pool.draw()
