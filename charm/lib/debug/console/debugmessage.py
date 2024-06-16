from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from arcade.types import RGBANormalized

from arcade import color as colors

import arrow
from imgui_bundle import imgui, imgui_ctx
from charm.lib import logging


def level_to_color(level: int) -> RGBANormalized:
    level_to_color_dict = {
        logging.COMMENT: colors.LIGHT_GRAY.normalized,
        logging.COMMAND: colors.PASTEL_YELLOW.normalized,
        logging.DEBUG: colors.BABY_BLUE.normalized,
        logging.INFO: colors.WHITE.normalized,
        logging.WARNING: colors.YELLOW.normalized,
        logging.ERROR: colors.RED.normalized,
        logging.FATAL: colors.MAGENTA.normalized
    }
    return level_to_color_dict.get(level, colors.GREEN.normalized)


def level_to_prefix(level: int) -> str:
    level_to_color_dict = {
        logging.COMMENT: "$",
        logging.COMMAND: "#",
        logging.DEBUG: "DBG",
        logging.INFO: "INF",
        logging.WARNING: "WRN",
        logging.ERROR: "ERR",
        logging.FATAL: "!!!"
    }
    return level_to_color_dict.get(level, "???")


class DebugMessage:
    def __init__(self, message: str, level: int) -> None:
        self.message = message
        self.level = level
        self.time = arrow.now().format("HH:mm:ss")
        self.color = level_to_color(level)
        self.prefix = level_to_prefix(level)

    def draw(self) -> None:
        if self.level not in [logging.COMMAND, logging.COMMENT]:
            with imgui_ctx.push_style_color(imgui.Col_.text.value, imgui.ImVec4(*colors.PURPLE.normalized)):
                imgui.text_unformatted(self.time + " | ")

            imgui.same_line()

        with imgui_ctx.push_style_color(imgui.Col_.text.value, imgui.ImVec4(*self.color)):
            imgui.text_unformatted(self.prefix + " ")

        imgui.same_line()

        with imgui_ctx.push_style_color(imgui.Col_.text.value, imgui.ImVec4(*self.color)):
            imgui.text_unformatted(self.message)
