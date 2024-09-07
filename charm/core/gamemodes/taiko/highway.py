from typing import Any
from collections.abc import Generator, Sequence

from functools import cache
from importlib.resources import files
import logging

import PIL.Image

from arcade import LRBT, draw_arc_filled, draw_arc_outline, draw_circle_outline, draw_rect_filled, draw_circle_filled, Texture, color

from charm.lib.charm import load_missing_texture
from charm.lib.pool import SpritePool
from charm.lib.utils import img_from_path

from charm.core.generic import NoteSprite, AutoEngine, Engine, Highway
from .chart import TaikoChart, TaikoNoteType, TaikoNote

import charm.data.images.skins as skins

logger = logging.getLogger("charm")

@cache
def load_note_texture(note_type: str, height: int) -> Texture:
    image_name = f"{note_type}"
    try:
        image = img_from_path(files(skins) / "taiko" / f"{image_name}.png")
        if image.height != height:
            width = int((height / image.height) * image.width)
            image = image.resize((width, height), PIL.Image.LANCZOS)
    except Exception as e:  # noqa: BLE001
        logger.error(f"Unable to load texture: {image_name} | {e}")
        return load_missing_texture(height, height)
    return Texture(image)

TAIKO_LANE_COUNT = 1  #*


class TaikoHighway(Highway):
    def __init__(self, chart: TaikoChart, engine: Engine, pos: tuple[int, int], size: tuple[int, int] = None, gap: int = 5, viewport: float = 1):
        super().__init__(chart, engine, pos, size, gap, viewport)
        self.chart: TaikoChart
        self.notes: Sequence[TaikoNote]
        self.color = (0, 0, 0, 128)  # TODO: eventually this will be a scrolling image.

        # Generators are great for ease, but it means we can't really 'scrub' backwards through the song
        # So this is a patch job at best.
        self._note_generator: Generator[TaikoNote, Any, None] = (note for note in self.notes) # type: ignore[]
        self._note_pool: SpritePool[NoteSprite] = SpritePool([NoteSprite(x=-1000.0, y=-1000.0) for _ in range(1000)])
        self._next_note: TaikoNote | None = next(self._note_generator, None)

        # Auto highway viz
        self.auto = isinstance(Engine, AutoEngine)
        self.last_side_right = False
        self.visible_time = 1 / 6

    @property
    def horizontal_viewport(self) -> float:
        return self.viewport * (self.window.width / self.window.height)

    @property
    def strikeline_y(self) -> float:
        return self.w / 10

    @property
    def note_size(self) -> int:
        return int(self.h // TAIKO_LANE_COUNT)

    @property
    def px_per_s(self) -> float:
        return self.w / self.viewport

    def note_y(self, at: float) -> float:
        rt = at - self.song_time
        return (-self.px_per_s * rt) - self.strikeline_y + self.x

    def update(self, song_time: float) -> None:
        super().update(song_time)

        while self._next_note is not None and self._next_note.time <= (self.song_time + self.horizontal_viewport) and self._note_pool.has_free_slot():
            note = self._next_note
            sprite = self._note_pool.get()
            sprite.texture = load_note_texture(note.type, self.note_size)
            sprite.position = -self.note_y(note.time), self.y + (self.h / 2)
            sprite.scale = 1.5 if note.large else 1.0
            sprite.visible = True
            sprite.note = note

            self._next_note = next(self._note_generator, None)

        for sprite in self._note_pool.given_items:
            sprite.center_x = -self.note_y(sprite.note.time)
            if sprite.note.hit or sprite.note.time <= (song_time - 0.1):
                sprite.visible = False
                sprite.position = -1000.0, -1000.0
                self._note_pool.give(sprite)

    @property
    def pos(self) -> tuple[int, int]:
        return self._pos

    @pos.setter
    def pos(self, p: tuple[int, int]) -> None:
        self._pos = p

    def draw(self) -> None:
        with self.static_camera.activate():
            draw_rect_filled(LRBT(self.x, self.x + self.w, self.y, self.y + self.h), self.color)
            draw_circle_filled(self.strikeline_y, self.y + (self.h / 2), self.note_size, self.color)

            if self.engine and self.engine.last_note_hit and self.song_time - self.engine.last_note_hit.hit_time <= self.visible_time:
                if self.engine.last_note_hit.type == TaikoNoteType.DON:
                    if self.engine.last_note_hit.large:
                        draw_circle_filled(self.strikeline_y, self.y + (self.h / 2), self.note_size * 0.75, color.DEBIAN_RED)
                    elif self.last_side_right:
                        draw_arc_filled(self.strikeline_y, self.y + (self.h / 2), self.note_size * 2 * 0.75, self.note_size * 2 * 0.75, color.DEBIAN_RED, -90, 90)
                        self.last_side_right = False
                    else:
                        draw_arc_filled(self.strikeline_y, self.y + (self.h / 2), self.note_size * 2 * 0.75, self.note_size * 2 * 0.75, color.DEBIAN_RED, 90, 270)
                        self.last_side_right = True
                elif self.engine.last_note_hit.type == TaikoNoteType.KAT:
                    if self.engine.last_note_hit.large:
                        draw_circle_outline(self.strikeline_y, self.y + (self.h / 2), self.note_size, color.BRIGHT_CERULEAN, 10)
                    elif self.last_side_right:
                        draw_arc_outline(self.strikeline_y, self.y + (self.h / 2), self.note_size * 2, self.note_size * 2, color.BRIGHT_CERULEAN, -90, 90, 20)
                        self.last_side_right = False
                    else:
                        draw_arc_outline(self.strikeline_y, self.y + (self.h / 2), self.note_size * 2, self.note_size * 2, color.BRIGHT_CERULEAN, 90, 270, 20)
                        self.last_side_right = True

            self._note_pool.draw()

