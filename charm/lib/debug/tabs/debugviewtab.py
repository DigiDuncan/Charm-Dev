from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from charm.lib.digiwindow import DigiWindow

from imgui_bundle import imgui, imgui_ctx


class DebugViewTab:

    def __init__(self, win: DigiWindow) -> None:
        self._win = win

    def draw(self):
        with imgui_ctx.begin_tab_item(type(self._win.current_view()).__name__) as view_tab:
            pass
            imgui.separator()
