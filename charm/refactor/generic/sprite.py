from typing import NamedTuple
from arcade import Sprite, Texture

from charm.refactor.generic.chart import Note

# *: This needs to be skinnable
def get_note_color_by_beat(beat: int) -> tuple[int, int, int]:
    """Used for beat coloring, essentially tinting a note to reflect where it falls in a measure.
    This allows for reading patterns easier."""
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


class NoteSprite(Sprite):
    def __init__(self, x: float, y: float):
        super().__init__(center_x = x, center_y = y)
        self.note: Note = None  # type: ignore --


class StrikelineSprite(Sprite):
    def __init__(self,
                 x: float, y: float,
                 active_texture: Texture, inactive_texture: Texture,
                 active_alpha: int = 255, inactive_alpha: int = 64
    ):
        super().__init__(path_or_texture=inactive_texture, center_x=x, center_y=y)
        self._active: bool = False

        self._active_texture: Texture = active_texture
        self._inactive_texture: Texture = inactive_texture

        self._active_alpha: int = active_alpha
        self._inactive_alpha: int = inactive_alpha

        self.alpha = inactive_alpha

    @property
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, is_now_active: bool) -> None:
        if is_now_active:
            self._active = is_now_active
            self.texture = self._active_texture
            self.alpha = self._active_alpha
        else:
            self._active = False
            self.texture = self._inactive_texture
            self.alpha = self._inactive_alpha


class SustainTextures(NamedTuple):
    tail: Texture
    body: Texture
    cap: Texture


SustainTextureDict = dict[str, SustainTextures]


# TODO: better name?
class SustainSprites:
    def __init__(self, size: float, tail_spacing: float = 0.0, *, downscroll: bool = False):
        self.size = size
        self.down_scrolling: bool = downscroll

        self._cap: Sprite = Sprite(center_x=-1000)
        self._body: Sprite = Sprite(center_x=-1000)
        self._tail: Sprite = Sprite(center_x=-1000)

        self._tail_spacing: float = tail_spacing
        self._body_offset: float = 0.0
        self._cap_offset: float = 0.0

        self.note: Note = None # type: ignore --
        self._textures: SustainTextureDict = None # type: ignore --

        self.hide()

    def get_sprites(self) -> tuple[Sprite, ...]:
        return self._cap, self._body, self._tail

    def place(self, note: Note, x: float, y: float, length: float, textures: SustainTextureDict) -> None:
        # TODO: test assumption about texture sizes
        self.note = note
        self._textures = textures
        self.update_texture()

        body_size = length - textures['primary'].cap.height - self._tail_spacing
        self._body_offset = body_size / 2.0 + self._tail_spacing
        self._cap_offset = length - textures['primary'].cap.height / 2.0

        if self.down_scrolling:
            self._body_offset *= -1
            self._cap_offset *= -1

        # TODO: Add option to flip textures when down scrolling

        self._tail.position = x, y
        self._body.position = x, y - self._body_offset
        self._body.height = body_size
        self._cap.position = x, y - self._cap_offset

        self.show()
        if body_size <= 0.0:
            self._body.visible = False

    def update_sustain(self, y: float, length: float) -> None:
        body_size = length - self._textures['primary'].cap.height - self._tail_spacing
        self._body_offset = body_size / 2.0 + self._tail_spacing
        self._cap_offset = length - self._textures['primary'].cap.height / 2.0

        if self.down_scrolling:
            self._body_offset *= -1
            self._cap_offset *= -1

        self._tail.center_y = y
        self._body.center_y = y - self._body_offset
        self._body.height = body_size
        self._cap.center_y = y - self._cap_offset

        if body_size <= 0.0:
            self._body.visible = False

    def show(self) -> None:
        self._cap.visible = True
        self._body.visible = True
        self._tail.visible = True

    def hide(self) -> None:
        self._cap.visible = False
        self._body.visible = False
        self._tail.visible = False

    def update_texture(self) -> None:
        # TODO: Update to work better with dictionaries / be overridden by game modes
        if not self.note or not self._textures:
            return

        t = self._textures

        if self.note.missed:
            self._tail.texture = t.get('miss', t['primary']).tail
            self._body.texture = t.get('miss', t['primary']).body
            self._cap.texture = t.get('miss', t['primary']).cap
        elif self.note.hit:
            self._tail.texture = t.get('hit', t['primary']).tail
            self._body.texture = t.get('hit', t['primary']).body
            self._cap.texture = t.get('hit', t['primary']).cap
        else:
            self._tail.texture = t['primary'].tail
            self._body.texture = t['primary'].body
            self._cap.texture = t['primary'].cap
