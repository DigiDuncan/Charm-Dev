from __future__ import annotations

import re

from imgui_bundle import imgui


def filter_to_regex(filter_str: str) -> str:
    prefix, post_str = filter_str[:1], filter_str[1:]
    if prefix == "+":
        return r"^.*" + re.escape(post_str)
    if prefix == "-":
        return r"^((?!.*" + re.escape(post_str) + ".*).)*$"
    return filter_str


class Filter:
    input_text_size = 400

    def __init__(self):
        self._filter_str: str = ""
        self._filter_pattern: re.Pattern[str] | None = None

    def draw(self) -> None:
        imgui.push_item_width(self.input_text_size)
        changed, filter_str = imgui.input_text_with_hint("Filter", "+incl, -excl, or regex", self._filter_str)
        if changed:
            self.filter = filter_str

    @property
    def filter(self) -> str:
        return self._filter_str

    @filter.setter
    def filter(self, filter_str: str) -> None:
        regex_str = filter_to_regex(filter_str)
        try:
            filter_pattern = re.compile(regex_str)
        except re.error:
            return
        self._filter_str = filter_str
        self._filter_pattern = filter_pattern

    @property
    def filter_pattern(self) -> re.Pattern[str] | None:
        return self._filter_pattern

    def is_shown(self, item: str) -> bool:
        if self._filter_pattern is None:
            return True
        return self._filter_pattern.match(item) is not None
