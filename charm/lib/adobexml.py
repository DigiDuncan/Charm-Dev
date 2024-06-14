from __future__ import annotations

from functools import cache
import logging
import math
from os import PathLike
from pathlib import Path
from importlib.resources import files, as_file
import re
from typing import Literal, NotRequired, Self, TypedDict, cast
import xml.etree.ElementTree as ET

import PIL.Image
import PIL.ImageDraw

import arcade
from arcade import Sprite, Texture, color as colors
from arcade.hitbox import HitBox

import charm.data.images.spritesheets

logger = logging.getLogger("charm")


OffsetsDict = dict[str, tuple[int, int]]
Anchor = Literal["left", "right", "bottom", "top", "center_x", "center_y"]

re_subtexture_name = re.compile(r"(.+?)(\d+)$")


class SubtextureJson(TypedDict):
    name: str
    x: str
    y: str
    width: str
    height: str
    frame_x: NotRequired[str]
    frame_y: NotRequired[str]
    frame_width: NotRequired[str]
    frame_height: NotRequired[str]


class Subtexture:
    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        width: int,
        height: int ,
        frame_x: int | None,
        frame_y: int | None,
        frame_width: int | None,
        frame_height: int | None,
        offset_x: int | None ,
        offset_y: int | None
    ):
        self.raw_name = name
        name_re = re_subtexture_name.match(self.raw_name)
        if name_re is None:
            raise ValueError(f"{name} is not a valid Subtexture name.")
        self.name = name_re.group(1)
        self.index = int(name_re.group(2))
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.frame_x = frame_x
        self.frame_y = frame_y
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.offset_x = offset_x
        self.offset_y = offset_y

    @classmethod
    def parse(cls, data: SubtextureJson, offsets: OffsetsDict) -> Self:
        name: str = data["name"]
        x = int(data["x"])
        y = int(data["y"])
        width = int(data["width"])
        height = int(data["height"])
        frame_x = int(data["frameX"]) if "frameX" in data else None
        frame_y = int(data["frameY"]) if "frameY" in data else None
        frame_width = int(data["frameWidth"]) if "frameWidth" in data else None
        frame_height = int(data["frameHeight"]) if "frameHeight" in data else None
        return cls(name, x, y, width, height, frame_x, frame_y, frame_width, frame_height, *offsets.get(name, (None, None)))

    def load_texture(self, image_path: Path, *, debug: bool = False) -> Texture:
        tx = arcade.load_texture(image_path, x = self.x, y = self.y, width = self.width, height = self.height)
        if self.frame_width is not None and self.frame_height is not None and self.frame_x is not None and self.frame_y is not None:
            # FIXME: I'm essentially abusing .load_texture() here.
            # I should probably be doing the cropping and caching myself,
            # but I trust Arcade to do it better than I can, so I end up making
            # a texture here and basically throwing it away.
            # This also noticably increases load time the first time you load
            # a paticular AdobeSprite.
            im = PIL.Image.new("RGBA", (self.frame_width, self.frame_height))
            im.paste(tx.image, (-self.frame_x, -self.frame_y))
            tx = Texture(im)
        if debug:
            draw = PIL.ImageDraw.ImageDraw(tx.image)
            draw.rectangle((0, 0, tx.image.width - 1, tx.image.height - 1), outline = colors.RED)
        return tx

    def __str__(self):
        return f"<Subtexture {self.raw_name}>"

    def __repr__(self) -> str:
        return str(self)


def load_offsets(path: Path) -> OffsetsDict:
    if not path.exists():
        return {}
    return parse_offsets(path.read_text(encoding="utf-8"))


def parse_offsets(data: str) -> OffsetsDict:
    splitdata = [line.split() for line in data.splitlines()]
    return {name: (int(offsetx), int(offsety)) for name, offsetx, offsety in splitdata}


class AdobeTextureAtlas:
    def __init__(self, image_path: str, subtextures: list[Subtexture]):
        self.image_path = image_path
        self.subtextures = subtextures

    @property
    def width(self) -> int:
        return max(h for st in self.subtextures for h in (st.width, st.frame_width) if h is not None)

    @property
    def height(self) -> int:
        return max(h for st in self.subtextures for h in (st.height, st.frame_height) if h is not None)

    @classmethod
    def parse(cls, s: str, offsets: OffsetsDict) -> AdobeTextureAtlas:
        tree = ET.ElementTree(ET.fromstring(s))
        root = tree.getroot()
        image_path: str = root.attrib["imagePath"]
        subtextures = [
            Subtexture.parse(cast(SubtextureJson, subtexture.attrib), offsets)
            for subtexture in root.iter("SubTexture")
        ]
        return cls(image_path, subtextures)


class AdobeSprite(Sprite):
    def __init__(self, folder_str: PathLike[str], name: str, anchors: tuple[Anchor], *, debug: bool = False):
        folder = Path(folder_str)
        xml_path = folder / f"{name}.xml"
        image_path = folder / f"{name}.png"
        offset_path = folder / f"{name}.offsets"

        with xml_path.open("r", encoding="utf-8") as f:
            xml = f.read()

        offsets = load_offsets(offset_path)
        ata = AdobeTextureAtlas.parse(xml, offsets)

        super().__init__(image_width=ata.width, image_height=ata.height, hit_box_algorithm=None)

        self.texture_map = {st: n for n, st in enumerate(ata.subtextures)}
        for st in ata.subtextures:
            self.append_texture(st.load_texture(image_path, debug=debug))
        self.set_texture(0)

        self.animations = {st.name for st in self.texture_map}

        self._current_animation: list[int] = []
        self._current_once_animation: list[int] = []
        self._current_animation_override: list[int] = []
        self._current_animation_sts: list[Subtexture] = []
        self._current_animation_index: int = 0
        self.fps: int = 24
        self._animation_time: float = 0

        self.anchors = anchors

    def cache_textures(self) -> None:
        # TODO: Can be very slow.
        for texture in self.textures:
            self.texture = texture
            self.hit_box = HitBox(self.texture.hit_box_points, (self.center_x, self.center_y))

    def set_animation(self, name: str) -> None:
        self._current_animation = []
        self._current_animation_sts = []
        for st, n in self.texture_map.items():
            if st.name == name:
                self._current_animation.append(n)
                self._current_animation_sts.append(st)
        self._current_animation_index = -1
        self._animation_time = math.inf

    def set_animation_override(self, name: str) -> None:
        self._current_animation_override = []
        for st, n in self.texture_map.items():
            if st.name == name:
                self._current_animation_override.append(n)
        self._current_animation_index = -1
        self._animation_time = math.inf

    def clear_animation_override(self) -> None:
        self._current_animation_override = []
        self._current_animation_index = -1
        self._animation_time = math.inf

    def play_animation_once(self, name: str) -> None:
        self._current_once_animation = []
        for st, n in self.texture_map.items():
            if st.name == name:
                self._current_once_animation.append(n)
        self._animation_time = math.inf

    def update_animation(self, delta_time: float = 1/60) -> None:
        self._animation_time += delta_time
        if self.fps == 0:
            return
        anchorable: dict[Anchor, float] = {
            "left": self.left,
            "right": self.right,
            "bottom": self.bottom,
            "top": self.top,
            "center_x": self.center_x,
            "center_y": self.center_y
        }
        if self._animation_time >= 1 / abs(self.fps):
            # Get anchors
            old_anchor_values: dict[Anchor, float] = {name: anchorable[name] for name in self.anchors}
            # Is there an animation override to be played once?
            if self._current_once_animation:
                self.set_texture(self._current_once_animation.pop(0))
                self.hit_box = HitBox(self.texture.hit_box_points, (self.center_x, self.center_y))
                self._animation_time = 0
            # If not, an animation override?
            elif self._current_animation_override:
                if self.fps > 0:
                    self._current_animation_index += 1
                else:
                    self._current_animation_index -= 1
                self._current_animation_index %= len(self._current_animation_override)

                self.set_texture(self._current_animation_override[self._current_animation_index])
                self.hit_box = HitBox(self.texture.hit_box_points, (self.center_x, self.center_y))
                self._animation_time = 0
            # If not, is there a normal animation?
            elif self._current_animation:
                if self.fps > 0:
                    self._current_animation_index += 1
                else:
                    self._current_animation_index -= 1
                self._current_animation_index %= len(self._current_animation)

                self.set_texture(self._current_animation[self._current_animation_index])
                self.hit_box = HitBox(self.texture.hit_box_points, (self.center_x, self.center_y))
                self._animation_time = 0
            # Set anchors
            for name, value in old_anchor_values.items():
                setattr(self, name, value)


@cache
def sprite_from_adobe(name: str, anchors: tuple[Anchor] = ("bottom",), *, debug: bool = False) -> AdobeSprite:
    with as_file(files(charm.data.images.spritesheets) / f"{name}.xml") as p:
        folder = p.parent
        return AdobeSprite(folder, name, anchors, debug=debug)
