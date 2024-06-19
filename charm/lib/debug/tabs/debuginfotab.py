from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from charm.lib.digiwindow import DigiWindow

from collections import deque

import numpy as np
from imgui_bundle import imgui, imgui_ctx


class DebugInfoTab:
    def __init__(self, window: DigiWindow) -> None:
        self.window = window
        self.beat_list = deque[float]()
        self.fps_list = deque[float]()
        self.local_time: float = 0.0

    def on_update(self, delta_time: float) -> None:
        # Beat Graph
        self.beat_list.append(self.window.theme_song.beat_factor)
        if len(self.beat_list) > 240:
            self.beat_list.popleft()

        # FPS Graph
        curr_fps = 1 / delta_time
        self.fps_list.append(curr_fps)
        if len(self.fps_list) > 240:
            self.fps_list.popleft()

        # localtime
        cv = self.window.current_view()
        self.localtime = cv.local_time if cv is not None else 0.0

    def draw(self) -> None:
        with imgui_ctx.begin_tab_item("Info") as info:
            if not info:
                return
            imgui.text("Info")
            imgui.text(f"Current Resolution: {self.window.size}")
            imgui.text("Egg Roll: 🥚")
            imgui.text(f"Current BPM: {self.window.theme_song.current_bpm}")
            # Beat Graph
            imgui.plot_lines( # type: ignore
                label="Beat",
                values=np.array(self.beat_list, np.float32),
                scale_min = 0,
                scale_max = 1,
            )
            imgui.text(f"Local Time: {self.localtime:.3f}")
            imgui.text(f"Song Time: {self.window.theme_song.time:.3f}")
            # FPS Graph
            imgui.plot_lines( # type: ignore
                label="FPS",
                values=np.array(self.fps_list, np.float32),
                scale_min = 120,
                scale_max = 240,
            )
            imgui.spacing()
            imgui.separator()
            imgui.text(f"{self.window.ctx.limits.RENDERER}")
