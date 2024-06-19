from __future__ import annotations

from imgui_bundle import imgui_ctx

from ..console.console import cons

class DebugLogTab:
    def __init__(self) -> None:
        pass

    def on_update(self, delta_time: float) -> None:
        pass

    def draw(self) -> None:
        with imgui_ctx.begin_tab_item("Log") as log:
            if not log:
                return
            cons.draw()
