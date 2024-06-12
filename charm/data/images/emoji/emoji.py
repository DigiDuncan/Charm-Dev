from collections.abc import Callable
from typing import Any, TypedDict, cast

import json
import logging
from pathlib import Path
import re
from functools import cache

import emoji_data_python
import pyglet
from pyglet.image import AbstractImage, load
from pyglet.text.formats.structured import ImageElement
from pyglet.text import Label

logger = logging.getLogger("charm")


class RegionJson(TypedDict):
    name: str
    emoji_width: int
    emoji_height: int
    emojis: list[str]

class EmojiPicker:
    def __init__(self, sheet: AbstractImage, region_data: RegionJson):
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
        inserts: list[tuple[int, ImageElement]] = []
        emojized_string = emoji_data_python.replace_colons(s)
        while m := re.search(emoji_data_python.get_emoji_regex(), emojized_string):
            emojized_string = re.sub(emoji_data_python.get_emoji_regex(), "", emojized_string)
            inserts.append((m.start(1), self.get_emoji_element(m.group(1))))
            logger.debug(f"Found emoji in string {s}...")
        logger.debug(f"Found {len(inserts)} emojis!")
        logger.debug(f"String is now: {emojized_string}")
        return emojized_string, inserts


with Path("./twemoji.json").open("r") as f:
    region_data: RegionJson = json.load(f)
logger.debug("Loaded emoji JSON...")

with Path("./twemoji.png").open("rb") as f:
    image = load("twemoji.png", file=f)
logger.debug("Loaded emoji PNG...")

emoji_picker = EmojiPicker(image, region_data)
logger.debug("Loaded emoji picker...")


def copy_sig[**P, T](fn_to_copy: Callable[P, T]) -> Callable[[Callable[..., Any]], Callable[P, T]]:
    def copier(fn: Callable[..., Any]) -> Callable[P, T]:
        return cast(Callable[P, T], fn)
    return copier

class EmojiLabel(Label):
    @copy_sig(Label.__init__)
    def __init__(self, text: str, *args: Any, **kwargs: Any): # noqa: ANN401
        super().__init__(text, *args, **kwargs)
        old_text = text
        new_text, inserts = emoji_picker.get_clean_string(self.text)
        self.text = new_text

        doc = self.document
        for pos, i in inserts:
            logger.debug(f"Inserting {i.image} at pos {pos}...")
            doc.insert_element(pos, i)

        self.document = doc
        logger.debug(f"Created label for string {old_text}!")
        x = [(e.position, e.image) for e in cast(list[ImageElement], self.document._elements)]  # noqa: SLF001
        logger.debug(x)


def main() -> None:
    window = pyglet.window.Window()
    label = EmojiLabel("wow :smile: I can smile", color = (255, 255, 255, 255), x = 320, y = 240, font_size = 48)

    @window.event
    def on_draw() -> None: # pyright: ignore reportUnusedFunction
        window.clear()
        label.draw()


    pyglet.app.run()


if __name__ == "__main__":
    main()
