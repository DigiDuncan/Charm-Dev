from __future__ import annotations
from collections.abc import Iterable
from typing import Literal, get_args
import arcade.key
from arcade.key import \
    A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z, \
    GRAVE, KEY_1, KEY_2, KEY_3, KEY_4, KEY_5, KEY_6, KEY_7, KEY_8, KEY_9, KEY_0, MINUS, EQUAL, \
    F1, F2, F3, F4, F5, F6, F7, F8, F9, F10, F11, F12, \
    F13, F14, F15, F16, F17, F18, F19, F20, F21, F22, F23, F24, \
    RETURN, ENTER, ESCAPE, BACKSPACE, SPACE, UP, DOWN, LEFT, RIGHT, F11, \
    MOD_SHIFT, RSHIFT

from charm.lib.errors import TooManyKeyBindError, ConflictingKeyBindError, \
    MissingRequiredKeyBindError

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

# FLAGS
REQUIRED = 1
SINGLEBIND = 2

# CONTEXTS
Context = Literal["global", "hero", "fourkey"]
GLOBAL, HERO, FOURKEY = get_args(Context)


class Action:
    def __init__(self, keymap: KeyMap, name: str, defaults: Iterable[KeyMod | Key], flags: int = 0, context: Context = GLOBAL) -> None:
        self._keymap = keymap
        self._keymap.actions.append(self)
        self._name = name
        self._defaults: list[KeyMod] = [to_keymod(k) for k in defaults]
        self.keys: list[KeyMod] = []
        self._required = bool(flags & REQUIRED)
        self._singlebind = bool(flags & SINGLEBIND)
        self._context: Context = context
        self.set_defaults()
        self.v_missing = False
        self.v_toomany = False
        self.conflicting_keys: set[KeyMod] = set()

    @property
    def v_conflict(self) -> bool:
        return len(self.conflicting_keys) > 0

    def _bind(self, key: KeyMod) -> None:
        """Bind a key to this Action"""
        if key in self.keys:
            return
        self.keys.append(key)
        if key not in self._keymap.keys:
            self._keymap.keys[key] = []
        self._keymap.keys[key].append(self)
        if key not in self._keymap.context_keys[self._context]:
            self._keymap.context_keys[self._context][key] = []
        self._keymap.context_keys[self._context][key].append(self)
        self._validate(key)

    def _unbind(self, key: KeyMod) -> None:
        """Unbind a key from this Action"""
        if key not in self.keys:
            return
        self.keys.remove(key)
        self._keymap.keys[key].remove(self)
        self._keymap.context_keys[self._context][key].remove(self)
        self._validate(key)

    def _validate(self, key: KeyMod) -> None:
        """Update validation flags"""
        self.v_missing = self._required and len(self.keys) == 0
        self.v_toomany = self._singlebind and len(self.keys) > 1
        self._validate_conflicts(key)

    def _validate_conflicts(self, key: KeyMod) -> None:
        """Update v_conflict validation flag"""
        actions = self._get_context_actions_by_key(key)
        if self not in actions:
            self.conflicting_keys.discard(key)
        has_conflict = len(actions) > 1
        for action in actions:
            if has_conflict:
                action.conflicting_keys.add(key)
            else:
                action.conflicting_keys.discard(key)

    def _get_context_actions_by_key(self, key: KeyMod) -> list[Action]:
        """Get all Actions by key that are in a related context"""
        if self._context == GLOBAL:
            actions = self._keymap.keys[key]
        else:
            actions = self._keymap.context_keys[GLOBAL][key] + self._keymap.context_keys[self._context][key]
        return actions

    def bind(self, key: KeyMod | Key) -> None:
        """Bind a key to this Action"""
        km = to_keymod(key)
        self._bind(km)

    def unbind(self, key: KeyMod | Key) -> None:
        """Unbind a key from this Action"""
        km = to_keymod(key)
        self._unbind(km)

    def unbind_all(self) -> None:
        """Unbind all keys from this Action"""
        for key in list(self.keys):
            self._unbind(key)

    def set_defaults(self) -> None:
        """Set all key bindings on this Action to default"""
        self.unbind_all()
        for key in self._defaults:
            self._bind(key)

    @property
    def pressed(self) -> bool:
        for k, m in self.keys:
            if k in self._keymap.pressed and self._keymap.pressed[k] == m:
                return True
        return False

    @property
    def released(self) -> bool:
        for k, m in self.keys:
            if k in self._keymap.released and self._keymap.released[k] == m:
                return True
        return False

    @property
    def held(self) -> bool:
        for k, m in self.keys:
            if k in self._keymap.held and self._keymap.held[k] == m:
                return True
        return False

    def __str__(self) -> str:
        return f"{self._name}: {[get_keyname(k) for k in self.keys]}"

class KeyMap:
    def __init__(self):
        """Access and set mappings for inputs to actions. Key binding."""
        self.actions: list[Action] = []
        self.keys: dict[KeyMod, list[Action]] = {}
        self.pressed: dict[Key, Mod] = {}
        self.released: dict[Key, Mod] = {}
        self.held: dict[Key, Mod] = {}
        self.context_keys: dict[Context, dict[KeyMod, list[Action]]] = {
            GLOBAL: {},
            FOURKEY: {},
            HERO: {}
        }

        self.start =         Action(self, 'start',         [RETURN, ENTER],     REQUIRED)
        self.back =          Action(self, 'back',          [ESCAPE, BACKSPACE], REQUIRED)
        self.navup =         Action(self, 'navup',         [UP],                REQUIRED)
        self.navdown =       Action(self, 'navdown',       [DOWN],              REQUIRED)
        self.navleft =       Action(self, 'navleft',       [LEFT],              SINGLEBIND)
        self.navright =      Action(self, 'navright',      [RIGHT],             SINGLEBIND)
        self.seek_zero =     Action(self, 'seek_zero',     [KEY_0],             SINGLEBIND)
        self.seek_backward = Action(self, 'seek_backward', [MINUS],             SINGLEBIND)
        self.seek_forward =  Action(self, 'seek_forward',  [EQUAL],             SINGLEBIND)
        self.pause =         Action(self, 'pause',         [SPACE],             REQUIRED | SINGLEBIND)
        self.fullscreen =    Action(self, 'fullscreen',    [F11],               REQUIRED | SINGLEBIND)
        self.mute =          Action(self, 'mute',          [M],                 REQUIRED | SINGLEBIND)

        self.debug =                   Action(self, 'debug',                   [GRAVE])
        self.log_sync =                Action(self, 'log_sync',                [S],              SINGLEBIND)
        self.toggle_distractions =     Action(self, 'toggle_distractions',     [KEY_8],          SINGLEBIND)
        self.toggle_chroma =           Action(self, 'toggle_chroma',           [B],              SINGLEBIND)
        self.debug_toggle_hit_window = Action(self, 'debug_toggle_hit_window', [(H, MOD_SHIFT)], SINGLEBIND)
        self.debug_show_results =      Action(self, 'debug_show_results',      [(R, MOD_SHIFT)], SINGLEBIND)
        self.dump_textures =           Action(self, 'dump_textures',           [E],              SINGLEBIND)
        self.debug_toggle_flags =      Action(self, 'debug_toggle_flags',      [F],              SINGLEBIND)
        self.debug_e =                 Action(self, 'debug_e',                 [E],              SINGLEBIND)
        self.debug_f24 =               Action(self, 'debug_f24',               [F24],            SINGLEBIND)
        self.toggle_show_text =        Action(self, 'toggle_show_text',        [T],              SINGLEBIND)

        self.fourkey_1 =       Action(self, 'fourkey_1',       [D],      SINGLEBIND, context=FOURKEY)
        self.fourkey_2 =       Action(self, 'fourkey_2',       [F],      SINGLEBIND, context=FOURKEY)
        self.fourkey_3 =       Action(self, 'fourkey_3',       [J],      SINGLEBIND, context=FOURKEY)
        self.fourkey_4 =       Action(self, 'fourkey_4',       [K],      SINGLEBIND, context=FOURKEY)

        self.hero_1 =          Action(self, 'hero_1',          [KEY_1],  SINGLEBIND, context=HERO)
        self.hero_2 =          Action(self, 'hero_2',          [KEY_2],  SINGLEBIND, context=HERO)
        self.hero_3 =          Action(self, 'hero_3',          [KEY_3],  SINGLEBIND, context=HERO)
        self.hero_4 =          Action(self, 'hero_4',          [KEY_4],  SINGLEBIND, context=HERO)
        self.hero_5 =          Action(self, 'hero_5',          [KEY_5],  SINGLEBIND, context=HERO)
        self.hero_strum_up =   Action(self, 'hero_strum_up',   [UP],     SINGLEBIND, context=HERO)
        self.hero_strum_down = Action(self, 'hero_strum_down', [DOWN],   SINGLEBIND, context=HERO)
        self.hero_power =      Action(self, 'hero_power',      [RSHIFT], SINGLEBIND, context=HERO)

        self.fourkey: FourKeyAliasMap = FourKeyAliasMap(self)
        self.hero: HeroAliasMap = HeroAliasMap(self)

    def unbind(self, key: Key | KeyMod) -> None:
        """Unbind a particular key"""
        km = to_keymod(key)
        if km not in self.keys:
            return
        for action in self.keys[km]:
            action.unbind(km)

    def unbind_all(self) -> None:
        """Unbind all actions."""
        for action in self.actions:
            action.unbind_all()

    def set_defaults(self) -> None:
        """Rebind all actions to their defaults."""
        for action in self.actions:
            action.set_defaults()

    def __str__(self) -> str:
        return f"{[str(act) for act in self.actions]}"

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
