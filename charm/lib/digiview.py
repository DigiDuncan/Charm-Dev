from __future__ import annotations
from typing import Concatenate
from collections.abc import Callable

from dataclasses import dataclass
import functools
import logging
import traceback

import arcade
from imgui_bundle import imgui
from arcade import LBWH, LRBT, Rect, View

from charm.lib.charm import CharmColors
from charm.lib.component_manager import ComponentManager
from charm.lib.anim import ease_linear, perc
from charm.lib.digiwindow import DigiWindow
from charm.lib.errors import CharmException, GenericError
from charm.lib.keymap import keymap
from charm.lib.sfxmanager import SfxManager

logger = logging.getLogger("charm")


def shows_errors[S: DigiView, **P](fn: Callable[Concatenate[S, P], None]) -> Callable[Concatenate[S, P], None]:
    return fn
    @functools.wraps(fn)
    def wrapper(self: S, *args: P.args, **kwargs: P.kwargs) -> None:
        try:
            fn(self, *args, **kwargs)
        except Exception as e:  # noqa: BLE001
            if not isinstance(e, CharmException):
                e = GenericError(e)
            if not self.shown and self.back is not None:
                self = self.back
            self.on_error(e)
            logger_fn = {
                "error": logger.error,
                "warn": logger.warn,
                "info": logger.info
            }.get(e.icon_name, logger.info)
            logger_fn(f"{e.title}: {e.message}")
            logger.debug(traceback.format_exc())
    return wrapper


def ignore_imgui[**P](fn: Callable[P, None]) -> Callable[P, None]:
    @functools.wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> None:
        if imgui.is_window_hovered(imgui.HoveredFlags_.any_window.value):
            return
        fn(*args, **kwargs)
    return wrapper


@dataclass
class ErrorPopup:
    error: CharmException
    expiry: float


class DigiView(View):
    def __init__(
        self,
        *,
        back: DigiView | None = None,
        fade_in: float = 0
    ):
        super().__init__()
        self.window: DigiWindow
        self.back = back
        self.shown = False
        self._errors: list[ErrorPopup] = []  # [error, seconds to show]
        self.local_start: float = 0
        self.fader = Fader(self, fade_in)
        self.components = ComponentManager()

    @property
    def sfx(self) -> SfxManager:
        return self.window.sfx

    @property
    def size(self) -> tuple[int, int]:
        return self.window.size

    @property
    def local_time(self) -> float:
        return self.window.time - self.local_start

    def on_error(self, error: CharmException) -> None:
        offset = len(self._errors) * 4
        error.sprite.center_x += offset
        error.sprite.center_y += offset
        self._errors.append(ErrorPopup(error, self.local_time + 3))
        self.sfx.error.play()

    def presetup(self) -> None:
        """Must be called at the beginning of setup()"""
        self.local_start = self.window.time
        arcade.set_background_color(CharmColors.FADED_GREEN)
        self.components.reset()

    def setup(self) -> None:
        pass

    def postsetup(self) -> None:
        """Must be called at the end of setup()"""
        self.on_resize(*self.window.size)

    def on_show_view(self) -> None:
        self.shown = True

    def on_resize(self, width: int, height: int) -> None:
        self.window.camera.position = self.window.center
        self.window.camera.projection = LRBT(-width/2, width/2, -height/2, height/2)
        self.window.camera.viewport = LBWH(0, 0, width, height)
        self.fader.on_resize(width, height)
        self.components.on_resize(width, height)

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        keymap.on_key_press(symbol, modifiers)
        if keymap.debug.pressed:
            self.window.debug.enabled = not self.window.debug.enabled
        elif keymap.fullscreen.pressed:
            self.window.set_fullscreen(not self.window.fullscreen)
        elif keymap.mute.pressed:
            self.window.theme_song.volume = 0
        super().on_key_press(symbol, modifiers)

    def on_key_release(self, symbol: int, modifiers: int) -> None:
        keymap.on_key_release(symbol, modifiers)
        super().on_key_release(symbol, modifiers)

    def on_update(self, delta_time: float) -> None:
        self._errors = [popup for popup in self._errors if popup.expiry < self.local_time]
        self.fader.on_update(delta_time)
        self.components.on_update(delta_time)

    def predraw(self) -> None:
        self.window.camera.use()
        self.clear()

    def on_draw(self) -> None:
        self.predraw()
        self.postdraw()

    def postdraw(self) -> None:
        self.components.on_draw()
        for popup in self._errors:
            popup.error.sprite.draw()
        self.window.debug.draw()
        self.fader.on_draw()

    def go_back(self) -> None:
        if self.back is None:
            return
        self.back.setup()
        self.window.show_view(self.back)
        self.sfx.back.play()

    def goto(self, dest: DigiView) -> None:
        dest.setup()
        self.window.show_view(dest)


class Fader:
    def __init__(self, view: DigiView, fade_in: float):
        self.view = view
        self.fade_in = fade_in
        self.color = (0, 0, 0, 255)
        self.screen: Rect
        self.on_resize(*self.view.size)

    @property
    def visible(self) -> bool:
        return self.view.local_time <= self.fade_in

    def on_update(self, delta_time: float) -> None:
        if not self.visible:
            return
        p = perc(0, self.fade_in, self.view.local_time)
        alpha = ease_linear(255, 0, p)
        self.color = (0, 0, 0, int(alpha))

    def on_resize(self, width: int, height: int) -> None:
        self.screen = LBWH(0, 0, width, height)

    def on_draw(self) -> None:
        if not self.visible:
            return
        arcade.draw_rect_filled(self.screen, self.color)
