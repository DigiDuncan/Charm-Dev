
# pyright: reportMissingTypeStubs=true
from __future__ import annotations
from typing import TYPE_CHECKING, Concatenate
if TYPE_CHECKING:
    from collections.abc import Callable
    from charm.lib.digiwindow import DigiWindow
    from arcade import Rect

import time
from dataclasses import dataclass
import functools
import logging

import arcade
from imgui_bundle import imgui
from arcade import LBWH, LRBT, View, SpriteList

from charm.lib.charm import CharmColors
from charm.lib.components import ComponentManager
from charm.lib.anim import ease_linear, perc
from charm.lib.errors import CharmError, GenericError, log_charmerror
from charm.lib.keymap import KeyMap
from charm.lib.sfxmanager import SFXManager

logger = logging.getLogger("charm")


def shows_errors[S: DigiView, **P](fn: Callable[Concatenate[S, P], None]) -> Callable[Concatenate[S, P], None]:
    @functools.wraps(fn)
    def wrapper(self: S, *args: P.args, **kwargs: P.kwargs) -> None:
        try:
            fn(self, *args, **kwargs)
        except Exception as e:  # noqa: BLE001
            if not isinstance(e, CharmError):
                e = GenericError(e)
            if (not self.shown) and self.back is not None:
                self = self.back
            self.on_error(e)
            log_charmerror(e)
    return wrapper


def disable_when_focus_lost[**P](*, keyboard: bool = False, mouse: bool = False) -> Callable[[Callable[P, None]], Callable[P, None]]:
    def wrapper(fn: Callable[P, None]) -> Callable[P, None]:
        @functools.wraps(fn)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> None:
            if mouse and imgui.get_io().want_capture_mouse:
                return
            if keyboard and imgui.get_io().want_capture_keyboard:
                return
            fn(*args, **kwargs)
        return wrapped
    return wrapper


@dataclass
class ErrorPopup:
    error: CharmError
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
        self._error_list: SpriteList = SpriteList()
        self.local_start: float = 0
        self.fader = Fader(self, fade_in)
        self.components = ComponentManager()
        self.debug_timer = DebugTimer()
        self.last_error: CharmError | None = None

    @property
    def sfx(self) -> SFXManager:
        return self.window.sfx

    @property
    def size(self) -> tuple[int, int]:
        return self.window.size

    @property
    def local_time(self) -> float:
        return self.window.time - self.local_start

    def on_error(self, error: CharmError) -> None:
        if self.last_error and (self.last_error.title, self.last_error.message) == (error.title, error.message) and self.last_error in [e.error for e in self._errors]:
            error.repeat = self.last_error.repeat + 1
            error.redraw()
        else:
            offset = len(self._errors) * 4
            error.sprite.center_x += offset
            error.sprite.center_y += offset
            self.sfx.error.play()
        self._errors.append(ErrorPopup(error, self.local_time + 3))
        self._error_list.append(error.sprite)
        self.last_error = error

    def presetup(self) -> None:
        """Must be called at the beginning of setup()"""
        self.debug_timer.setup_start()
        self.local_start = self.window.time
        self.setup_end = None
        self.draw_start = None
        self.draw_end = None
        arcade.set_background_color(CharmColors.FADED_GREEN)

    def setup(self) -> None:
        pass

    def postsetup(self) -> None:
        """Must be called at the end of setup()"""
        self.on_resize(*self.window.size)
        self.debug_timer.setup_end()

    def on_show_view(self) -> None:
        self.shown = True

    def on_resize(self, width: int, height: int) -> None:
        self.window.camera.position = self.window.center
        self.window.camera.projection = LRBT(-width/2, width/2, -height/2, height/2)
        self.window.camera.viewport = LBWH(0, 0, width, height)
        self.fader.on_resize(width, height)
        self.components.on_resize(width, height)

    @shows_errors
    def on_button_press(self, keymap: KeyMap) -> None:
        pass

    @shows_errors
    def on_button_release(self, keymap: KeyMap) -> None:
        pass

    def on_update(self, delta_time: float) -> None:
        for popup in self._errors[:]:
            if popup.expiry < self.local_time:
                self._errors.remove(popup)
                self._error_list.remove(popup.error.sprite)
        self.fader.on_update(delta_time)
        self.components.on_update(delta_time)

    def predraw(self) -> None:
        self.debug_timer.draw_start()
        self.window.default_camera.use()
        self.clear()

    def on_draw(self) -> None:
        self.predraw()
        self.postdraw()

    def postdraw(self) -> None:
        self.components.draw()
        self._error_list.draw()
        self.window.debug.draw()
        self.fader.on_draw()
        self.debug_timer.draw_end()

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

        # Manually managing blend should not be needed if we're passing in an alpha value
        self.view.window.ctx.enable(self.view.window.ctx.BLEND)
        self.view.window.ctx.blend_func = self.view.window.ctx.BLEND_DEFAULT
        arcade.draw_rect_filled(self.screen, self.color)


class DebugTimer:
    def __init__(self):
        self.setup_start_time = None
        self.setup_end_time = None
        self.draw_start_time = None
        self.draw_end_time = None

    def setup_start(self) -> None:
        self.setup_start_time = time.time()
        self.setup_end_time = None
        self.draw_start_time = None
        self.draw_end_time = None
        logger.debug("SETUP START")

    def setup_end(self) -> None:
        if self.setup_end_time is not None or self.setup_start_time is None:
            return
        self.setup_end_time = time.time()
        duration = self.setup_end_time - self.setup_start_time
        logger.debug(f"SETUP END: DURATION={int(duration*1000)}ms")

    def draw_start(self) -> None:
        if self.draw_start_time is not None or self.setup_end_time is None:
            return
        self.draw_start_time = time.time()
        duration = self.draw_start_time - self.setup_end_time
        logger.debug(f"DRAW START: DELAY={int(duration*1000)}ms")

    def draw_end(self) -> None:
        if self.draw_end_time is not None or self.draw_start_time is None:
            return
        self.draw_end_time = time.time()
        duration = self.draw_end_time - self.draw_start_time
        logger.debug(f"DRAW END: DURATION={int(duration*1000)}ms")
