from __future__ import annotations
from weakref import WeakMethod
from typing import Callable, Literal
from enum import StrEnum


__all__ = (
    'Settings',
    'settings'
)


class Setting[T]:

    def __init__(self, default: T, is_settable: bool = True) -> None:
        self._listeners: list[WeakMethod[Callable[[SettingsBase], None]]] = []  # Should maybe be a weakref?
        self._value = default
        self._default = default
        self._is_settable: bool = is_settable

    def __get__(self, obj, objtype=None) -> T:
        if obj is None:
            return self  # type: ignore -- -.- please type checker
        return self._value
    
    def __set__(self, obj, value: T):
        if obj is None:
            raise ValueError('Cannot set a setting using the Settings type, use an instance of it instead.')
        if not self._is_settable:
            raise ValueError('This setting cannot be set') # TODO: use the name magic stuff to get the setting name
        if value == self._value:
            return

        self._value = value
        for listener in self._listeners[:]:
            f = listener()
            if f is None:
                self._listeners.remove(listener)
                continue
            f(obj)

    def __delete__(self, obj):
        self._listeners = []

    def add_listener(self, listener: Callable[[SettingsBase], None]):
        self._listeners.append(WeakMethod(listener))

    def remove_listener(self, listener: Callable[[SettingsBase], None]):
        self._listeners.remove(listener)  # type: ignore -- Actually weakrefs match the eqality of their internal object, and clearly the function must still exsist.


class SettingsBase:
    @classmethod
    def add_listeners(cls, *settings: Setting):
        # Decorator to add multiple listeners
        def _add(listener: Callable[[SettingsBase], None]):
            for setting in settings:
                setting.add_listener(listener)
            return listener
        return _add


class Volume:
    master = Setting[float](0.4)
    music = Setting[float](1.0)
    sfx = Setting[float](1.0)
    menu = Setting[float](1.0)

class Mixer(StrEnum):
    default = 'default'
    master = 'master'
    music = 'music'
    sfx = 'sfx'
    menu = 'menu'
MixerNames = Literal["default", "master", "music", "sound", "menu_music"]

class Window:
    title = Setting[str]("Charm", False)
    size = Setting[tuple[int, int]]((1280, 720))
    resolution = Setting[tuple[int, int]]((1280, 720))  # Maybe one day won't be 1:1 with size
    ups = Setting[int](10000)
    fps = Setting[int](120)


class Settings(SettingsBase):
    # Put all the settings here
    volume = Volume()
    window = Window()

    # put all settings methods here
    def get_volume(self, mixer: Mixer):
        match mixer:
            case Mixer.default | Mixer.master:
                # default is actually 1 * master, but that is equivalent
                return self.volume.master
            case Mixer.music:
                return self.volume.master * self.volume.music
            case Mixer.sfx:
                return self.volume.master * self.volume.sfx
            case Mixer.menu:
                return self.volume.master * self.volume.menu


settings: Settings = Settings()