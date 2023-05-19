from functools import cache
import logging
import math
from os import PathLike
from pathlib import Path
import importlib.resources as pkg_resources
import re
import xml.etree.ElementTree as ET

import PIL.Image
import PIL.ImageDraw

from arcade import Sprite
import arcade

import charm.data.images.spritesheets

logger = logging.getLogger("charm")

subtexture_name = re.compile(r"(.+?)(\d+)$")


def strint(i: int | str | None) -> int | None:
    """Convert a str to an int, or return an existing int or None."""
    if isinstance(i, int) or i is None:
        return i
    elif isinstance(i, str):
        return int(i)
    else:
        raise ValueError(f"{i} is not a int or str.")


class Subtexture:
    def __init__(self, name: str, x: int | str, y: int | str, width: int | str, height: int | str,
                 frame_x: int | str = None, frame_y: int | str = None, frame_width: int | str = None, frame_height: int | str = None,
                 offset_x: int | str = None, offset_y: int | str = None):
        self._name = name
        name_re = subtexture_name.match(self._name)
        if name_re is None:
            raise ValueError(f"{name} is not a valid Subtexture name.")
        self.name = name_re.group(1)
        self.index = strint(name_re.group(2))

        self.x = strint(x)
        self.y = strint(y)
        self.width = strint(width)
        self.height = strint(height)
        self.frame_x = strint(frame_x)
        self.frame_y = strint(frame_y)
        self.frame_width = strint(frame_width)
        self.frame_height = strint(frame_height)
        self.offset_x = strint(offset_x)
        self.offset_y = strint(offset_y)

    def __str__(self):
        return f"<Subtexture {self._name}>"

    def __repr__(self) -> str:
        return str(self)


class AdobeTextureAtlas:
    def __init__(self, image_path: str, subtextures: list[Subtexture]):
        self.image_path = image_path
        self.subtextures = subtextures

    @property
    def width(self):
        return max([st.frame_width for st in self.subtextures if st.frame_width is not None] + [st.width for st in self.subtextures if st.width is not None])

    @property
    def height(self):
        return max([st.frame_height for st in self.subtextures if st.frame_height is not None] + [st.height for st in self.subtextures if st.height is not None])

    @classmethod
    def parse(cls, s: str, offsets: str = "") -> "AdobeTextureAtlas":
        tree = ET.ElementTree(ET.fromstring(s))
        root = tree.getroot()
        image_path = root.attrib["imagePath"]
        offsets = offsets.splitlines() if offsets else None

        subtextures: list[Subtexture] = []
        for subtexture in root.iter("SubTexture"):
            st = subtexture.attrib
            name = st["name"]
            x = st["x"]
            y = st["y"]
            width = st["width"]
            height = st["height"]
            frame_x = st.get("frameX", None)
            frame_y = st.get("frameY", None)
            frame_width = st.get("frameWidth", None)
            frame_height = st.get("frameHeight", None)
            ox = None
            oy = None
            if offsets:
                for offset in offsets:
                    if offset.startswith(name):
                        n, ox, oy = offset.split()
            subtextures.append(Subtexture(
                name, x, y, width, height, frame_x, frame_y, frame_width, frame_height, ox, oy
            ))

        return cls(image_path, subtextures)


class AdobeSprite(Sprite):
    def __init__(self, folder_path: PathLike, name: str, anchors = ["bottom"], debug = False):
        self.folder = Path(folder_path)
        self._xml_path = self.folder / f"{name}.xml"
        self._image_path = self.folder / f"{name}.png"
        self._offset_path = self.folder / f"{name}.offsets"
        with open(self._xml_path, "r", encoding="utf-8") as f:
            self._xml = f.read()
        self._offsets = ""
        if self._offset_path.exists():
            with open(self._offset_path, "r", encoding="utf-8") as f:
                self._offsets = f.read()
        self._ata = AdobeTextureAtlas.parse(self._xml, offsets=self._offsets)
        self.texture_map: dict[Subtexture, int] = {}
        textures = []
        for n, st in enumerate(self._ata.subtextures):
            if st.frame_width is not None and st.frame_height is not None:
                # FIXME: I'm essentially abusing .load_texture() here.
                # I should probably be doing the cropping and caching myself,
                # but I trust Arcade to do it better than I can, so I end up making
                # a texture here and basically throwing it away.
                # This also noticably increases load time the first time you load
                # a paticular AdobeSprite.
                tx = arcade.load_texture(self._image_path, x = st.x, y = st.y, width = st.width, height = st.height)
                im = PIL.Image.new("RGBA", (st.frame_width, st.frame_height))
                im.paste(tx.image, (-st.frame_x, -st.frame_y))
                tx = arcade.Texture(im)
            else:
                tx = arcade.load_texture(self._image_path, x = st.x, y = st.y, width = st.width, height = st.height)
            if debug:
                draw = PIL.ImageDraw.ImageDraw(tx.image)
                draw.rectangle((0, 0, tx.image.width - 1, tx.image.height - 1), outline = arcade.color.RED)
            textures.append(tx)
            self.texture_map[st] = n

        super().__init__(image_width=self._ata.width, image_height=self._ata.height, hit_box_algorithm=None)
        for tx in textures:
            self.append_texture(tx)
        self.set_texture(0)
        self.animations = set([st.name for st in self.texture_map])

        self._current_animation = []
        self._current_once_animation = []
        self._current_animation_override = []
        self._current_animation_sts = []
        self._current_animation_index = 0
        self.fps = 24
        self._animation_time = 0

        self.anchors = anchors

    def cache_textures(self):
        # TODO: Can be very slow.
        for texture in self.textures:
            self.texture = texture
            self.hit_box = arcade.hitbox.HitBox(self.texture.hit_box_points, (self.center_x, self.center_y))
            # logger.info(f"Cached texture {texture.name}")

    def set_animation(self, name: str):
        self._current_animation = []
        self._current_animation_sts = []
        for st, n in self.texture_map.items():
            if st.name == name:
                self._current_animation.append(n)
                self._current_animation_sts.append(st)
        self._current_animation_index = -1
        self._animation_time = math.inf

    def set_animation_override(self, name: str):
        self._current_animation_override = []
        for st, n in self.texture_map.items():
            if st.name == name:
                self._current_animation_override.append(n)
        self._current_animation_index = -1
        self._animation_time = math.inf

    def clear_animation_override(self):
        self._current_animation_override = []
        self._current_animation_index = -1
        self._animation_time = math.inf

    def play_animation_once(self, name: str):
        self._current_once_animation = []
        for st, n in self.texture_map.items():
            if st.name == name:
                self._current_once_animation.append(n)
        self._animation_time = math.inf

    def update_animation(self, delta_time):
        self._animation_time += delta_time
        if self.fps == 0:
            return
        if self._animation_time >= 1 / abs(self.fps):
            # Get anchors
            if self.anchors:
                anchorlist = [getattr(self, a) for a in self.anchors]
            # Is there an animation override to be played once?
            if self._current_once_animation:
                self.set_texture(self._current_once_animation.pop(0))
                self.hit_box = arcade.hitbox.HitBox(self.texture.hit_box_points, (self.center_x, self.center_y))
                self._animation_time = 0
            # If not, an animation override?
            elif self._current_animation_override:
                if self.fps > 0:
                    self._current_animation_index += 1
                else:
                    self._current_animation_index -= 1
                self._current_animation_index %= len(self._current_animation_override)

                self.set_texture(self._current_animation_override[self._current_animation_index])
                self.hit_box = arcade.hitbox.HitBox(self.texture.hit_box_points, (self.center_x, self.center_y))
                self._animation_time = 0
            # If not, is there a normal animation?
            elif self._current_animation:
                if self.fps > 0:
                    self._current_animation_index += 1
                else:
                    self._current_animation_index -= 1
                self._current_animation_index %= len(self._current_animation)

                self.set_texture(self._current_animation[self._current_animation_index])
                self.hit_box = arcade.hitbox.HitBox(self.texture.hit_box_points, (self.center_x, self.center_y))
                self._animation_time = 0
            # Set anchors
            if self.anchors:
                for a, v in zip(self.anchors, anchorlist):
                    setattr(self, a, v)


@cache
def sprite_from_adobe(s: str, anchors: tuple[str] = ("bottom"), debug = False) -> AdobeSprite:
    with pkg_resources.path(charm.data.images.spritesheets, f"{s}.xml") as p:
        parent = p.parent
        return AdobeSprite(parent, s, anchors, debug)
