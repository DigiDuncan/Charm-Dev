from __future__ import annotations

import logging

from .console import cons


class ImGuiLogger(logging.Handler):
    def __init__(self, level: int | str = logging.NOTSET, *, showsource: bool = False):
        self.showsource = showsource
        super().__init__(level)

    def emit(self, record: logging.LogRecord) -> None:
        message = record.getMessage()
        if self.showsource:
            message = f"{record.name}: {message}"
        cons.add_log(message, record.levelno)
