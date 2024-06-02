from __future__ import annotations
from collections.abc import Iterable
import arcade.key
from arcade.key import \
    A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z, \
    GRAVE, KEY_1, KEY_2, KEY_3, KEY_4, KEY_5, KEY_6, KEY_7, KEY_8, KEY_9, KEY_0, MINUS, EQUAL, \
    F1, F2, F3, F4, F5, F6, F7, F8, F9, F10, F11, F12, \
    F13, F14, F15, F16, F17, F18, F19, F20, F21, F22, F23, F24, \
    RETURN, ENTER, ESCAPE, BACKSPACE, SPACE, UP, DOWN, LEFT, RIGHT, F11, \
    MOD_SHIFT, RSHIFT

from charm.lib.errors import MultipleKeyBindsError, ExclusiveKeyBindError, \
    KeyUnboundError, ActionNotFoundError, SetNotFoundError, ActionNotInSetError

Mod = int
Key = int
KeyMod = tuple[Key, Mod]

key_names = {v: k for k, v in arcade.key.__dict__.items() if isinstance(v, int) and not k.startswith("MOD_")}
mod_names = {v: k for k, v in arcade.key.__dict__.items() if isinstance(v, int) and k.startswith("MOD_") and k != "MOD_ACCEL"}

def get_keyname(k: Key | KeyMod) -> str:
    k, m = to_keymod(k)
    return " + ".join([mod_names[mod] for mod in split_mod(m)] + [key_names[k]])

def to_keymod(k: Key | KeyMod) -> KeyMod:
    if isinstance(k, Key):
        return (k, 0)
    return k

def split_mod(m: Mod) -> list[Mod]:
    mod_values = [1 << n for n in range(9)]
    return [n for n in mod_values if m & n]


REQUIRED = 1
SINGLEBIND = 2
EXCLUSIVE = 4

class Action:
    def __init__(self, keymap: KeyMap, name: str, defaults: Iterable[KeyMod | Key], flags: int = 0) -> None:
        self.keymap = keymap
        self.keymap.actions[self.name] = self
        self.name = name
        self.defaults: list[KeyMod] = [to_keymod(i) for i in defaults]
        self.keys: list[KeyMod] = []
        self.required = bool(flags & REQUIRED)
        self.singlebind = bool(flags & SINGLEBIND)
        self.exclusive = bool(flags & EXCLUSIVE)
        self.set_defaults()

    def _bind(self, key: KeyMod) -> None:
        self.keys.append(key)
        self.keymap.keys[key] = self

    def bind(self, key: KeyMod | Key) -> None:
        km = to_keymod(key)
        if km in self.keymap.keys:
            raise ValueError
        self._bind(km)

    def rebind(self, key: KeyMod | Key) -> None:
        km = to_keymod(key)
        if km in self.keymap.keys:
            self.keymap.unbind(km)
        self._bind(km)

    def unbind(self, key: KeyMod | Key) -> None:
        km = to_keymod(key)
        if km not in self.keys:
            return
        self.keys.remove(km)
        del self.keymap.keys[km]

    def unbind_all(self) -> None:
        for km in list(self.keys):
            self.unbind(km)

    def set_defaults(self) -> None:
        self.unbind_all()
        for km in self.defaults:
            self.bind(km)

    @property
    def pressed(self) -> bool:
        for k, m in self.keys:
            if k in self.keymap.pressed and self.keymap.pressed[k] == m:
                return True
        return False

    @property
    def released(self) -> bool:
        for k, m in self.keys:
            if k in self.keymap.released and self.keymap.released[k] == m:
                return True
        return False

    @property
    def held(self) -> bool:
        for k, m in self.keys:
            if k in self.keymap.held and self.keymap.held[k] == m:
                return True
        return False

    def __str__(self) -> str:
        return f"{self.name}: {[get_keyname(k) for k in self.keys]}"

    def validate(self) -> bool:
        """Check the action for errors."""
        # Action doesn't allow multiple binds, but there are
        if self.singlebind and len(self.keys) > 1:
            raise MultipleKeyBindsError(self.name)
        # Unbound
        if self.required and not self.keys:
            raise KeyUnboundError(self.name)
        # Exclusive key found on multiple actions
        for a in self.keymap.actions.values():
            for key in self.keys:
                if a.exclusive and key in a.keys:
                    raise ExclusiveKeyBindError(get_keyname(key), [a.name, self.name])
        return True


class KeyMap:
    def __init__(self):
        """Access and set mappings for inputs to actions. Key binding."""
        self.actions: dict[str, Action] = {}
        self.keys: dict[KeyMod, Action] = {}
        self.held: dict[Key, Mod] = {}
        self.pressed: dict[Key, Mod] = {}
        self.released: dict[Key, Mod] = {}

        self.start = Action(self, 'start', [RETURN, ENTER], REQUIRED | EXCLUSIVE)
        self.back = Action(self, 'back', [ESCAPE, BACKSPACE], REQUIRED | EXCLUSIVE)
        self.navup = Action(self, 'navup', [UP], REQUIRED | EXCLUSIVE)
        self.navdown = Action(self, 'navdown', [DOWN], REQUIRED | EXCLUSIVE)
        self.debug = Action(self, 'debug', [GRAVE], EXCLUSIVE)
        self.pause = Action(self, 'pause', [SPACE], REQUIRED | SINGLEBIND | EXCLUSIVE)
        self.fullscreen = Action(self, 'fullscreen', [F11], REQUIRED | SINGLEBIND | EXCLUSIVE)
        self.mute = Action(self, 'mute', [M], REQUIRED | SINGLEBIND | EXCLUSIVE)
        self.fourkey_1 = Action(self, 'fourkey_1', [D], SINGLEBIND)
        self.fourkey_2 = Action(self, 'fourkey_2', [F], SINGLEBIND)
        self.fourkey_3 = Action(self, 'fourkey_3', [J], SINGLEBIND)
        self.fourkey_4 = Action(self, 'fourkey_4', [K], SINGLEBIND)
        self.hero_1 = Action(self, 'hero_1', [KEY_1], SINGLEBIND)
        self.hero_2 = Action(self, 'hero_2', [KEY_2], SINGLEBIND)
        self.hero_3 = Action(self, 'hero_3', [KEY_3], SINGLEBIND)
        self.hero_4 = Action(self, 'hero_4', [KEY_4], SINGLEBIND)
        self.hero_5 = Action(self, 'hero_5', [KEY_5], SINGLEBIND)
        self.hero_strum_up = Action(self, 'hero_strum_up', [UP], SINGLEBIND)
        self.hero_strum_down = Action(self, 'hero_strum_down', [DOWN], SINGLEBIND)
        self.hero_power = Action(self, 'hero_power', [RSHIFT], SINGLEBIND)
        self.seek_zero = Action(self, 'seek_zero', [KEY_0], SINGLEBIND)
        self.seek_backward = Action(self, 'seek_backward', [MINUS], SINGLEBIND)
        self.seek_forward = Action(self, 'seek_forward', [EQUAL], SINGLEBIND)
        self.log_sync = Action(self, 'log_sync', [S], SINGLEBIND)
        self.toggle_distractions = Action(self, 'toggle_distractions', [KEY_8], SINGLEBIND)
        self.toggle_chroma = Action(self, 'toggle_chroma', [B], SINGLEBIND)
        self.debug_toggle_hit_window = Action(self, 'debug_toggle_hit_window', [(H, MOD_SHIFT)], SINGLEBIND)
        self.debug_show_results = Action(self, 'debug_show_results', [(R, MOD_SHIFT)], SINGLEBIND)
        self.dump_textures = Action(self, 'dump_textures', [E], SINGLEBIND)
        self.debug_toggle_flags = Action(self, 'debug_toggle_flags', [F], SINGLEBIND)
        self.navleft = Action(self, 'navleft', [LEFT], SINGLEBIND)
        self.navright = Action(self, 'navright', [RIGHT], SINGLEBIND)
        self.debug_e = Action(self, 'debug_e', [E], SINGLEBIND)
        self.debug_f24 = Action(self, 'debug_f24', [F24], SINGLEBIND)
        self.toggle_show_text = Action(self, 'toggle_show_text', [T], SINGLEBIND)

        self.fourkey: FourKeyAliasMap = FourKeyAliasMap(self)
        self.hero: HeroAliasMap = HeroAliasMap(self)

    def unbind(self, key: Key | KeyMod) -> None:
        km = to_keymod(key)
        self.keys[km].unbind(km)

    def unbind_all(self) -> None:
        """Remove all inputs from the '`name`' action."""
        for action in self.actions.values():
            action.unbind_all()

    def set_defaults(self) -> None:
        """Set all actions inputs to their default state."""
        for action in self.actions.values():
            action.set_defaults()

    def validate_all(self) -> bool:
        """Check all actions for errors."""
        for action in self.actions.values():
            action.validate()
        return True

    def __str__(self) -> str:
        return f"{[str(i) for i in self.actions]}"

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        self.pressed = {symbol: modifiers}
        self.held[symbol] = modifiers

    def on_key_release(self, symbol: int, modifiers: int) -> None:
        self.released = {symbol: modifiers}
        if symbol in self.held:
            del self.held[symbol]

class FourKeyAliasMap:
    def __init__(self, keymap: KeyMap):
        self.key1 = keymap.fourkey_1
        self.key2 = keymap.fourkey_2
        self.key3 = keymap.fourkey_3
        self.key4 = keymap.fourkey_4

    @property
    def state(self) -> list[bool]:
        return [self.key1.pressed, self.key2.pressed, self.key3.pressed, self.key4.pressed]

class HeroAliasMap:
    def __init__(self, keymap: KeyMap):
        self.green = keymap.hero_1
        self.red = keymap.hero_2
        self.yellow = keymap.hero_3
        self.blue = keymap.hero_4
        self.orange = keymap.hero_5
        self.strumup = keymap.hero_strum_up
        self.strumdown = keymap.hero_strum_down
        self.power = keymap.hero_power

    @property
    def state(self) -> list[bool]:
        return [
            self.green.pressed,
            self.red.pressed,
            self.yellow.pressed,
            self.blue.pressed,
            self.orange.pressed,
            self.strumup.pressed,
            self.strumdown.pressed,
            self.power.pressed
        ]

keymap = KeyMap()
