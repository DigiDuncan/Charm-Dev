import importlib.resources as pkg_resources
import json
import logging
import re
from functools import cache

import emoji_data_python
from pyglet.image import AbstractImage, load
from pyglet.text.formats.structured import ImageElement
from pyglet.text.document import AbstractDocument
from pyglet.text import Label

import charm.data.images.emoji

logger = logging.getLogger("charm")


def pt_to_px(pt: int) -> int:
    return round(pt * (4 / 3))


@cache
def pyglet_img_from_resource(package: pkg_resources.Package, resource: pkg_resources.Resource) -> AbstractImage:
    with pkg_resources.open_binary(package, resource) as f:
        image = load("unknown.png", file=f)
    return image


class EmojiPicker:
    def __init__(self, sheet: AbstractImage, region_data: dict):
        self.sheet = sheet
        self.region_data = region_data

        self.set_name: str = self.region_data["name"]
        self.emoji_width: int = self.region_data["emoji_width"]
        self.emoji_height: int = self.region_data["emoji_height"]
        self.emojis: list[str] = self.region_data["emojis"]

    @cache
    def get_emoji_coords(self, emoji: str) -> tuple[int, int]:
        grid_width = self.sheet.width // self.emoji_width

        index = self.emojis.index(emoji)
        row = index // grid_width
        col = index % grid_width
        return row * self.emoji_width, col * self.emoji_height

    def get_emoji_element(self, emoji: str) -> ImageElement:
        x, y = self.get_emoji_coords(emoji)
        img_region = self.sheet.get_region(x, y, self.emoji_width, self.emoji_height)
        element = ImageElement(image=img_region)
        logger.debug(f"Got emoji element for string {emoji}...")
        return element

    def get_clean_string(self, s: str) -> tuple[str, list[tuple[int, ImageElement]]]:
        inserts = []
        emojized_string = emoji_data_python.replace_colons(s)
        while m := re.search(emoji_data_python.get_emoji_regex(), emojized_string):
            emojized_string = re.sub(emoji_data_python.get_emoji_regex(), "", emojized_string)
            inserts.append((m.start(1), self.get_emoji_element(m.group(1))))
            logger.debug(f"Found emoji in string {s}...")
        logger.debug(f"Found {len(inserts)} emojis!")
        logger.debug(f"String is now: {emojized_string}")
        return emojized_string, inserts


rd = pkg_resources.read_text(charm.data.images.emoji, "twemoji.json")
region_data = json.loads(rd)
logger.debug("Loaded emoji JSON...")
png = pyglet_img_from_resource(charm.data.images.emoji, "twemoji.png")
logger.debug("Loaded emoji PNG...")

emoji_picker = EmojiPicker(png, region_data)
logger.debug("Loaded emoji picker...")


class EmojiLabel(Label):
    def __init__(self, text: str, *args, **kwargs):
        super().__init__(text, *args, **kwargs)
        old_text = text
        new_text, inserts = emoji_picker.get_clean_string(self.text)
        self.text = new_text

        doc: AbstractDocument = self.document
        for pos, i in inserts:
            logger.debug(f"Inserting {i.image} at pos {pos}...")
            doc.insert_element(pos, i)

        self.document = doc
        logger.debug(f"Created label for string {old_text}!")
        logger.debug([(e.position, e.image) for e in self.document._elements])
