from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from charm.lib.digiview import DigiView

import logging

import arcade
from arcade import Window, Camera2D

from charm.lib.sfxmanager import SfxManager
from charm.lib.debug_menu import DebugMenu
from charm.lib.presencemanager import PresenceManager
from charm.lib.themesong import ThemeSong
from charm.views.title import TitleView

logger = logging.getLogger("charm")

class DigiWindow(Window):
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
        self.camera = Camera2D()

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

    def save_atlas(self, name: str = "atlas.png") -> None:
        atlas_path = Path("debug") / name
        atlas_path.parent.mkdir(parents=True, exist_ok=True)
        self.ctx.default_atlas.save(atlas_path)

    def current_view(self) -> DigiView | None: # pyright: ignore [reportIncompatibleMethodOverride]
        return cast("DigiView | None", super().current_view)
