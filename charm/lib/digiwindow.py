from __future__ import annotations
from typing import TYPE_CHECKING, cast

from charm.lib.sfxmanager import SfxManager
from charm.views.title import TitleView
if TYPE_CHECKING:
    from charm.lib.digiview import DigiView

import logging
import random
import importlib.resources as pkg_resources

import arcade
from pyglet.media import Player

from charm.lib.debug_menu import DebugMenu
from charm.lib.anim import ease_expoout
from charm.lib.bpmanim import BPMAnimator
from charm.lib.errors import CharmException
from charm.lib.generic.song import BPMChangeEvent
from charm.lib.presencemanager import PresenceManager
import charm.data.audio

logger = logging.getLogger("charm")



class Eggs:
    TRICKY = 666


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

        # Egg roll
        self.egg_roll = random.randint(1, 1000)

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
        return cast(DigiView | None, super().current_view)


class ThemeSong:
    def __init__(self) -> None:
        with pkg_resources.path(charm.data.audio, "song.mp3") as p:
            song = arcade.Sound(p)
        try:
            self.player: Player = song.play(volume=0, loop=True)
        except Exception as err:
            raise CharmException(
                title="Song Failed",
                message="Failed to load theme song"
            ) from err
        bpm_events = [BPMChangeEvent(0, 120), BPMChangeEvent(3, 220)]
        self.beat_animator = BPMAnimator(bpm_events, ease_expoout)

    def on_update(self, delta_time: float) -> None:
        self.beat_animator.update(self.time)

    @property
    def beat_factor(self) -> float:
        return self.beat_animator.factor

    @property
    def time(self) -> float:
        return self.player.time

    @property
    def volume(self) -> float:
        return self.player.volume # type: ignore

    @volume.setter
    def volume(self, value: float) -> None:
        self.player.volume = value # type: ignore

    def seek(self, value: float) -> None:
        self.player.seek(value)

    @property
    def current_bpm(self) -> float:
        return self.beat_animator.current_bpm

