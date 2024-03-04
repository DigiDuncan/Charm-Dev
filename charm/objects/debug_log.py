import logging

import arcade
import arrow
import pyglet

"""This module is now deprecated in favor of the DebugMenu using pyimgui."""

class DebugMessage:
    def __init__(self, message: str, level: int = logging.INFO) -> None:
        self.message = message
        self.level = level
        self.time = arrow.now().format("HH:mm:ss")

    @property
    def color(self):
        match self.level:
            case logging.DEBUG:
                return arcade.color.BABY_BLUE
            case logging.INFO:
                return arcade.color.WHITE
            case logging.WARN:
                return arcade.color.YELLOW
            case logging.ERROR:
                return arcade.color.RED
            case logging.FATAL:
                return arcade.color.MAGENTA
            case _:
                return arcade.color.GREEN

    @property
    def prefix(self):
        match self.level:
            case logging.DEBUG:
                return "DBG"
            case logging.INFO:
                return "INF"
            case logging.WARN:
                return "WRN"
            case logging.ERROR:
                return "ERR"
            case logging.FATAL:
                return "!!!"
            case _:
                return "???"

    def render(self) -> str:
        return (f"{{background_color (0, 0, 0, 255)}}{{color (128, 0, 128, 255)}}"
                f"{self.time} | "
                f"{{background_color {self.color[:]}}}{{color (0, 0, 0, 255)}}"
                f"{self.prefix} "
                f"{{background_color (0, 0, 0, 255)}}{{color {self.color[:]}}}"
                f"{self.message}")


class DebugLog:
    def __init__(self) -> None:
        self.messages: list[DebugMessage] = []
        self.doc = pyglet.text.document.FormattedDocument()
        self.layout = pyglet.text.layout.TextLayout(self.doc, width=1280, multiline=True)

    def render(self) -> str:
        renderstr = "\n\n".join([m.render() for m in self.messages[-10:]])
        return renderstr

    def _log(self, message: str, level = logging.INFO):
        self.messages.append(DebugMessage(message, level))
        self.layout.document = pyglet.text.decode_attributed(self.render())


class PygletHandler(logging.Handler):
    def __init__(self, *args, showsource=False, **kwargs):
        self.showsource = showsource
        super().__init__(*args, **kwargs)

    def emit(self, record):
        debug_log = arcade.get_window().debug_log
        message = record.getMessage()
        if self.showsource:
            message = f"{record.name}: {message}"
        debug_log._log(message, level=record.levelno)
