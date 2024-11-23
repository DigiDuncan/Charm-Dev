from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from charm.core.digiwindow import DigiWindow

from imgui_bundle import imgui, imgui_ctx


class DebugSettingsTab:
    def __init__(self, window: DigiWindow) -> None:
        self.show_fps = False
        self.window = window

    def on_update(self, delta_time: float) -> None:
        pass

    def draw(self) -> None:
        with imgui_ctx.begin_tab_item("Settings") as settings:
            if not settings:
                return
            imgui.text("Settings")
            # Settings
            _, self.show_fps = imgui.checkbox("Show FPS", self.show_fps)
            imgui.spacing()
            imgui.separator()
            imgui.text("Tools")
            # Tools
            if imgui.button("Save atlas..."):
                self.window.save_atlas()
            imgui.spacing()
            imgui.separator()

