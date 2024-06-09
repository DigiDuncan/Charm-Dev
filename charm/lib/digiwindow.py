from __future__ import annotations
from typing import TYPE_CHECKING, cast

from charm.lib.sfxmanager import SfxManager
from charm.views.title import TitleView
if TYPE_CHECKING:
    from charm.lib.digiview import DigiView

import logging

import arcade

from charm.lib.debug_menu import DebugMenu
from charm.lib.presencemanager import PresenceManager
from charm.lib.themesong import ThemeSong

logger = logging.getLogger("charm")


class DigiWindow(arcade.Window):
    def __init__(self, size: tuple[int, int], title: str, fps_cap: int):
        super().__init__(*size, title, update_rate=1 / fps_cap, enable_polling=True, resizable=True)
        self.sfx = SfxManager()
        self.fps_cap = fps_cap
        self.initial_view: DigiView = TitleView()
        self.time = 0.0

        # Play music
        self.theme_song: ThemeSong = ThemeSong()

        # Discord RP
        self.presence = PresenceManager()
        self.presence.connect("1056710104348639305")
        self.presence.set(":jiggycat:")

        arcade.draw_text(" ", 0, 0)  # force font init (fixes lag on first text draw)

        # Cameras and text labels
        self.camera = arcade.camera.Camera2D()

        # Debug menu
        self.debug = DebugMenu(self)

    def setup(self) -> None:
        self.initial_view.setup()
        self.show_view(self.initial_view)

    def on_update(self, delta_time: float) -> None:
        self.time += delta_time
        self.presence.on_update(delta_time)
        self.debug.on_update(delta_time)
        self.theme_song.on_update(delta_time)

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)
        self.debug.on_resize(width, height)

    def save_atlas(self) -> None:
        self.ctx.default_atlas.save("atlas.png")

    def current_view(self) -> DigiView | None: # type: ignore
        return super().current_view # type: ignore
