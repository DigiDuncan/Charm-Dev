from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING, cast

from charm.lib.splashscreen import SplashView

if TYPE_CHECKING:
    from charm.lib.digiview import DigiView

import logging

import arcade
from arcade import Window, Camera2D

from charm.lib.digiview import DigiView
from charm.lib.keymap import KeyMap, keymap
from charm.lib.sfxmanager import SFXManager
from charm.lib.debug import DebugMenu
from charm.lib.presencemanager import PresenceManager
from charm.lib.themesong import ThemeSong
from charm.views.title import TitleView
from charm.lib.charm import GumWrapper

from charm.core.loading2 import CHART_LOADER

logger = logging.getLogger("charm")


class DigiWindow(Window):
    def __init__(self, size: tuple[int, int], title: str, ups_cap: int, fps_cap: int):
        super().__init__(*size, title, update_rate=1.0 / ups_cap, enable_polling=True, resizable=True, draw_rate=1.0 / fps_cap)
        # We only need one gum wrapper, it a view wants to draw it then draw it and update it otherwise ignore it.
        # We don't need 6+ instances of it hanging around making everything stinky
        self.wrapper = GumWrapper()

        self.register_event_type('on_button_press')
        self.register_event_type('on_button_release')
        self.push_handlers(self.on_button_press, self.on_button_release)

        keymap.set_window(self)
        self.push_handlers(keymap.on_key_press, keymap.on_key_release)

        self.ctx.default_atlas.resize((2048, 2048))
        self.sfx = SFXManager()
        self.fps_cap = fps_cap
        self.initial_view: DigiView = SplashView(TitleView)

        # Play music
        self.theme_song: ThemeSong = ThemeSong()

        # Discord RP
        self.presence = PresenceManager()
        # self.presence.connect("1056710104348639305")
        # self.presence.set(":jiggycat:")

        arcade.draw_text(" ", 0, 0)  # force font init (fixes lag on first text draw)

        # Cameras and text labels
        self.camera = Camera2D()

        # Debug menu
        self.debug = DebugMenu(self)

        CHART_LOADER.wake_loader()

    def setup(self) -> None:
        self.initial_view.setup()
        self.show_view(self.initial_view)

    def on_update(self, delta_time: float) -> None:
        self.presence.on_update(delta_time)
        self.debug.on_update(delta_time)
        self.theme_song.on_update(delta_time)

    def on_button_press(self, keymap: KeyMap) -> None:
        if keymap.debug.pressed:
            self.debug.enabled = not self.debug.enabled
        elif keymap.fullscreen.pressed:
            self.set_fullscreen(not self.fullscreen)
        elif keymap.mute.pressed:
            self.theme_song.volume = 0

    def on_button_release(self, keymap: KeyMap) -> None:
        pass

    def on_resize(self, width: int, height: int) -> None:
        self.debug.on_resize(width, height)

    def save_atlas(self, name: str = "atlas.png") -> None:
        atlas_path = Path("debug") / name
        atlas_path.parent.mkdir(parents=True, exist_ok=True)
        self.ctx.default_atlas.save(atlas_path, draw_borders=True)

    def current_view(self) -> DigiView | None:  # pyright: ignore [reportIncompatibleMethodOverride]
        return cast("DigiView | None", super().current_view)

    def on_move(self, x: int, y: int) -> bool | None:
        self.wrapper.window_position = x, y
        self.draw(0.0)

    def show_view(self, new_view: DigiView) -> None:
        if new_view.back is None and self.current_view() is not None:
            new_view.back = self.current_view()
        super().show_view(new_view)
