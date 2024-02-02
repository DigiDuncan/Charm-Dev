import importlib.resources as pkg_resources
import json
import logging
import re
from functools import cache

import emoji_data_python
from pyglet.image import AbstractImage, load
from pyglet.text.formats.structured import ImageElement
from pyglet.text.document import AbstractDocument, FormattedDocument
from pyglet.text import DocumentLabel

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
    def get_emoji_coords(self, emoji: str) -> tuple[int, int] | None:
        grid_width = self.sheet.width // self.emoji_width

        try:
            index = self.emojis.index(emoji)
        except ValueError:
            try:
                index = self.emojis.index(emoji.removesuffix("\ufe0f"))
            except ValueError:
                logger.debug(f"{emoji} is not in the data?!")
                return (0, 0)
        row = index // grid_width
        col = index % grid_width
        return col * self.emoji_width, self.sheet.height - (row * self.emoji_height) - self.emoji_height

    def get_emoji_element(self, emoji: str, size: int) -> ImageElement:
        x, y = self.get_emoji_coords(emoji)
        img_region = self.sheet.get_region(x, y, self.emoji_width, self.emoji_height)
        img = img_region.get_texture()
        img.width = pt_to_px(size)
        img.height = pt_to_px(size)
        element = ImageElement(image=img)
        return element

    def get_clean_string(self, s: str, size: int) -> tuple[str, list[tuple[int, ImageElement]]]:
        inserts = []
        emojized_string = emoji_data_python.replace_colons(s)
        while m := re.search(emoji_data_python.get_emoji_regex(), emojized_string):
            emojized_string = re.sub(emoji_data_python.get_emoji_regex(), "", emojized_string)
            inserts.append((m.start(1), self.get_emoji_element(m.group(1), size)))
        return emojized_string, inserts


def get_emoji_picker(id: str) -> EmojiPicker:
    rd = pkg_resources.read_text(charm.data.images.emoji, f"{id}.json")
    region_data = json.loads(rd)
    png = pyglet_img_from_resource(charm.data.images.emoji, f"{id}.png")
    return EmojiPicker(png, region_data)


emojisets = {}


class FormattedLabel(DocumentLabel):
    def __init__(self, text='',
                 font_name=None, font_size=None, bold=False, italic=False, stretch=False,
                 color=(255, 255, 255, 255),
                 x=0, y=0, z=0, width=None, height=None,
                 anchor_x='left', anchor_y='baseline',
                 align='left',
                 multiline=False, dpi=None, batch=None, group=None, rotation=0):
        """:Parameters:
            `text` : str
                Text to display.
            `font_name` : str or list
                Font family name(s).  If more than one name is given, the
                first matching name is used.
            `font_size` : float
                Font size, in points.
            `bold` : bool/str
                Bold font style.
            `italic` : bool/str
                Italic font style.
            `stretch` : bool/str
                 Stretch font style.
            `color` : (int, int, int, int)
                Font colour, as RGBA components in range [0, 255].
            `x` : int
                X coordinate of the label.
            `y` : int
                Y coordinate of the label.
            `z` : int
                Z coordinate of the label.
            `width` : int
                Width of the label in pixels, or None
            `height` : int
                Height of the label in pixels, or None
            `anchor_x` : str
                Anchor point of the X coordinate: one of ``"left"``,
                ``"center"`` or ``"right"``.
            `anchor_y` : str
                Anchor point of the Y coordinate: one of ``"bottom"``,
                ``"baseline"``, ``"center"`` or ``"top"``.
            `align` : str
                Horizontal alignment of text on a line, only applies if
                a width is supplied. One of ``"left"``, ``"center"``
                or ``"right"``.
            `multiline` : bool
                If True, the label will be word-wrapped and accept newline
                characters.  You must also set the width of the label.
            `dpi` : float
                Resolution of the fonts in this layout.  Defaults to 96.
            `batch` : `~pyglet.graphics.Batch`
                Optional graphics batch to add the label to.
            `group` : `~pyglet.graphics.Group`
                Optional graphics group to use.
            `rotation`: float
                The amount to rotate the label in degrees. A positive amount
                will be a clockwise rotation, negative values will result in
                counter-clockwise rotation.

        """
        doc = FormattedDocument(text)
        super().__init__(doc, x, y, z, width, height, anchor_x, anchor_y, multiline, dpi, batch, group, rotation)

        self.document.set_style(0, len(self.document.text), {
            'font_name': font_name,
            'font_size': font_size,
            'bold': bold,
            'italic': italic,
            'stretch': stretch,
            'color': color,
            'align': align,
        })


class EmojiLabel(FormattedLabel):
    def __init__(self, text: str, *args, emojiset: str = "twemoji", **kwargs):
        super().__init__(text, *args, **kwargs)
        if emojiset in emojisets:
            emoji_picker = emojisets[emojiset]
        else:
            emojisets[emojiset] = get_emoji_picker(emojiset)
            emoji_picker = emojisets[emojiset]

        new_text, inserts = emoji_picker.get_clean_string(self.text, self.font_size)
        self.text = new_text

        doc: AbstractDocument = self.document
        for pos, i in inserts:
            doc.insert_element(pos, i)

        self.document = doc
