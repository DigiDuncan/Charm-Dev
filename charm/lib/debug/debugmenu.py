from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from imgui_bundle.python_backends.pyglet_backend import PygletProgrammablePipelineRenderer
    from charm.lib.digiwindow import DigiWindow

import pyglet

from imgui_bundle.python_backends.pyglet_backend import create_renderer
from imgui_bundle import imgui, ImVec2, imgui_ctx

from .overlaycamera import OverlayCamera
from .tabs.debugsettingstab import DebugSettingsTab
from .tabs.debuginfotab import DebugInfoTab
from .tabs.debugviewtab import DebugViewTab
from .tabs.debuglogtab import DebugLogTab
from .fpscounter import FPSCounter

import logging
logger = logging.getLogger("charm")


class DebugMenu:
    def __init__(self, window: DigiWindow) -> None:
        self.camera = OverlayCamera()
        self._enabled = False
        imgui.create_context()
        imgui.get_io().display_size = imgui.ImVec2(100, 100)
        imgui.font_atlas_get_tex_data_as_rgba32(imgui.get_io().fonts) # type: ignore
        self.impl: PygletProgrammablePipelineRenderer = create_renderer(window) # type: ignore
        self.settings_tab = DebugSettingsTab(window)
        self.info_tab = DebugInfoTab(window)
        self.view_tab = DebugViewTab(window)
        self.log_tab = DebugLogTab()
        self.fps_counter = FPSCounter()
        self.debug_label = pyglet.text.Label(
            "DEBUG",
            font_name='bananaslip plus',
            font_size=12,
            multiline=True, width=window.width,
            anchor_x='left', anchor_y='top',
            color=(0, 0, 0, 0xFF)
        )
        self.alpha_label = pyglet.text.Label(
            "ALPHA",
            font_name='bananaslip plus',
            font_size=16,
            anchor_x='right', anchor_y='bottom',
            color=(0, 0, 0, 32)
        )

    @property
    def show_fps(self) -> bool:
        return self.settings_tab.show_fps or self.enabled

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value
        # I shouldn't have to set these manually, but imgui only updates them during a imgui.new_frame().
        # So when we stop calling imgui.new_frame(), imgui locks all input.
        if not self._enabled:
            imgui.get_io().want_capture_keyboard = False
            imgui.get_io().want_capture_mouse = False

    def on_update(self, delta_time: float) -> None:
        self.settings_tab.on_update(delta_time)
        self.info_tab.on_update(delta_time)
        self.log_tab.on_update(delta_time)
        self.fps_counter.enabled = self.show_fps
        self.fps_counter.on_update(delta_time)

    def on_resize(self, width: int, height: int) -> None:
        self.fps_counter.on_resize(width, height)
        self.debug_label.position = (0, height - self.fps_counter.fps_label.content_height - 5, 0)
        self.alpha_label.position = (width - 5, 5, 0)

    def draw(self) -> None:
        with self.camera.activate():
            self.fps_counter.draw()
            self.alpha_label.draw()
            if not self.enabled:
                return
            self.debug_label.draw()
            self.impl.process_inputs()

            imgui.new_frame()
            imgui.set_next_window_size(ImVec2(550, 350), imgui.Cond_.first_use_ever.value)

            with imgui_ctx.begin("Charm Debug Menu", True) as window:
                if not window.opened:
                    self.enabled = False
                self.draw_tab_bar()

            imgui.render()
            self.impl.render(imgui.get_draw_data())

    def draw_tab_bar(self) -> None:
        with imgui_ctx.begin_tab_bar("Options") as tab_bar:
            if not tab_bar:
                return
            self.settings_tab.draw()
            self.info_tab.draw()
            self.log_tab.draw()
            self.view_tab.draw()
