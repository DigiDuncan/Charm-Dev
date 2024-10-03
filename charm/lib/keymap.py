from __future__ import annotations
from logging import getLogger
from collections.abc import Iterable
from typing import Literal, cast, get_args

from arcade import Vec2
from pyglet.input import get_controllers
from pyglet.input.base import Controller

from arcade.future.input.inputs import MouseAxes, MouseButtons, Keys, ControllerButtons, ControllerAxes # noqa: F401

import charm.lib.data

logger = getLogger('charm')

type Modifiers = Literal[0, Keys.MOD_SHIFT, Keys.MOD_CTRL, Keys.MOD_ALT, Keys.MOD_CAPSLOCK, Keys.MOD_NUMLOCK, Keys.MOD_WINDOWS, Keys.MOD_COMMAND, Keys.MOD_OPTION, Keys.MOD_SCROLLLOCK]
type Button = Keys | ControllerButtons
type KeyMod = tuple[Button, int]

mod_names = {v.value: v.name for v in get_args(Modifiers) if v in Keys}

def get_keyname(k: KeyMod) -> str:
    key, mods = to_keymod(k)
    return " + ".join([mod_names[mod] for mod in split_mod(mods)] + [key.name])

def to_keymod(k: Button | KeyMod) -> KeyMod:
    if isinstance(k, Keys) or isinstance(k, ControllerButtons):
        return (k, 0)
    return k

def split_mod(m: int) -> list[int]:
    mod_values = [1 << n for n in range(9)]
    return [n for n in mod_values if m & n]


# FLAGS
REQUIRED = 1
SINGLEBIND = 2

# CONTEXTS
Context = Literal["global", "hero", "fourkey", "menu", "parallax", "songmenu"]
ALL = None

# CONSTS
TRIGGER_DEADZONE = 0.05
STICK_DEADZONE = 0.05

ActionJson = tuple[KeyMod, ...]
KeyMapJson = dict[str, ActionJson]


class KeyStateManager:
    def __init__(self):
        self.pressed: dict[Button, int] = {}
        self.released: dict[Button, int] = {}
        self.held: dict[Button, int] = {}
        self.ignore_mods = Keys.MOD_CAPSLOCK.value | Keys.MOD_NUMLOCK.value | Keys.MOD_SCROLLLOCK.value

    def on_button_press(self, symbol: Button, modifiers: int) -> None:
        logger.info(f'Button {symbol} pressed with mods {modifiers}')
        modifiers = modifiers & ~self.ignore_mods
        self.pressed = {symbol: modifiers}
        self.held[symbol] = modifiers

    def on_button_release(self, symbol: Button, modifiers: int) -> None:
        logger.info(f'Button {symbol} released with mods {modifiers}')
        modifiers = modifiers & ~self.ignore_mods
        self.released = {symbol: modifiers}
        if symbol in self.held:
            del self.held[symbol]

    def is_input_pressed(self, button: KeyMod) -> bool:
        k, m = button
        return k in self.pressed and self.pressed[k] == m

    def is_input_released(self, button: KeyMod) -> bool:
        k, m = button
        return k in self.released and self.released[k] == m

    def is_input_held(self, button: KeyMod) -> bool:
        k, m = button
        return k in self.held and self.held[k] == m


class Action:
    def __init__(self, keymap: KeyMap, id: str, defaults: Iterable[Button | KeyMod], flags: int = 0, context: Context = "global") -> None:
        self._keymap = keymap
        self.id = id
        self._defaults: list[KeyMod] = [to_keymod(k) for k in defaults]
        self.keys: set[KeyMod] = set()
        self._required = bool(flags & REQUIRED)
        self._singlebind = bool(flags & SINGLEBIND)
        self._context: Context = context
        self.v_missing = False
        self.v_toomany = False
        self.conflicting_keys: set[KeyMod] = set()
        self._keymap.add_action(self)

    @property
    def v_conflict(self) -> bool:
        return len(self.conflicting_keys) > 0

    def _bind(self, key: KeyMod) -> None:
        """Bind a key to this Action"""
        if key in self.keys:
            return
        self.keys.add(key)
        self._keymap.add_key(key, self, self._context)
        self._validate(key)

    def _unbind(self, key: KeyMod) -> None:
        """Unbind a key from this Action"""
        if key not in self.keys:
            return
        self.keys.discard(key)
        self._keymap.remove_key(key, self, self._context)
        self._validate(key)

    def _validate(self, key: KeyMod) -> None:
        """Update validation flags"""
        self.v_missing = self._required and len(self.keys) == 0
        self.v_toomany = self._singlebind and len(self.keys) > 1
        self._validate_conflicts(key)

    def _validate_conflicts(self, key: KeyMod) -> None:
        """Update v_conflict validation flag"""
        actions = self._keymap.get_actions(key, self._context)
        if self not in actions:
            self.conflicting_keys.discard(key)
        has_conflict = len(actions) > 1
        for action in actions:
            if has_conflict:
                action.conflicting_keys.add(key)
            else:
                action.conflicting_keys.discard(key)

    def bind(self, key: KeyMod | Button) -> None:
        """Bind a key to this Action"""
        key = to_keymod(key)
        self._bind(key)

    def unbind(self, key: KeyMod | Button) -> None:
        """Unbind a key from this Action"""
        key = to_keymod(key)
        self._unbind(key)

    def unbind_all(self) -> None:
        """Unbind all keys from this Action"""
        for key in list(self.keys):
            self._unbind(key)

    def set_defaults(self) -> None:
        """Set all key bindings on this Action to default"""
        self.unbind_all()
        for key in self._defaults:
            self._bind(key)

    def to_json(self) -> ActionJson:
        return tuple(sorted(self.keys))

    def set_from_json(self, data: ActionJson) -> None:
        self.unbind_all()
        for key in data:
            self.bind(key)

    def __lt__(self, other: Action) -> bool:
        if isinstance(other, Action):
            return self.id < other.id
        raise NotImplementedError

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Action):
            return self.id == other.id
        return False

    def __hash__(self) -> int:
        return hash(self.id)

    @property
    def pressed(self) -> bool:
        return any(self._keymap.state.is_input_pressed(key) for key in self.keys)

    @property
    def released(self) -> bool:
        return any(self._keymap.state.is_input_released(key) for key in self.keys)

    @property
    def held(self) -> bool:
        return any(self._keymap.state.is_input_held(key) for key in self.keys)

    def __str__(self) -> str:
        return f"{self.id}: {[get_keyname(k) for k in self.keys]}"


class SubKeyMap[T]:
    def __init__(self, *actions: Action):
        self.actions = actions

    @property
    def state(self) -> T:
        return cast(T, tuple(a.held for a in self.actions))

    @property
    def pressed_action(self) -> Action | None:
        for a in self.actions:
            if a.pressed:
                return a
        return None

    @property
    def released_action(self) -> Action | None:
        for a in self.actions:
            if a.released:
                return a
        return None


class KeyMap:
    def __init__(self):
        """Access and set mappings for inputs to actions. Key binding."""
        self.actions: set[Action] = set()
        self.keys: dict[Context | None, dict[KeyMod, set[Action]]] = {ctx: {} for ctx in [*get_args(Context), None]}
        self.state = KeyStateManager()
        self.bound_controller: Controller = None
        self.dpad: Vec2 = Vec2()
        self.triggers: list[float] = [0.0, 0.0]
        self.l_stick: Vec2 = Vec2()
        self.r_stick: Vec2 = Vec2()

        self.start =         Action(self, 'start',         [Keys.RETURN, Keys.ENTER],     REQUIRED)
        self.back =          Action(self, 'back',          [Keys.ESCAPE, Keys.BACKSPACE], REQUIRED)
        self.pause =         Action(self, 'pause',         [Keys.SPACE],             REQUIRED)
        self.fullscreen =    Action(self, 'fullscreen',    [Keys.F11],               REQUIRED)
        self.mute =          Action(self, 'mute',          [Keys.M],                 REQUIRED)

        self.navup =         Action(self, 'navup',         [Keys.UP],                REQUIRED, context="menu")
        self.navdown =       Action(self, 'navdown',       [Keys.DOWN],              REQUIRED, context="menu")
        self.navleft =       Action(self, 'navleft',       [Keys.LEFT],              REQUIRED, context="menu")
        self.navright =      Action(self, 'navright',      [Keys.RIGHT],             REQUIRED, context="menu")

        self.seek_zero =     Action(self, 'seek_zero',     [Keys.KEY_0])
        self.seek_backward = Action(self, 'seek_backward', [Keys.MINUS])
        self.seek_forward =  Action(self, 'seek_forward',  [Keys.EQUAL])

        self.debug =                   Action(self, 'debug',                   [Keys.GRAVE])
        self.log_sync =                Action(self, 'log_sync',                [Keys.S]            )
        self.toggle_distractions =     Action(self, 'toggle_distractions',     [Keys.KEY_8]        )
        self.toggle_chroma =           Action(self, 'toggle_chroma',           [Keys.B]            )
        self.debug_toggle_hit_window = Action(self, 'debug_toggle_hit_window', [(Keys.H, Keys.MOD_SHIFT.value)])
        self.debug_show_results =      Action(self, 'debug_show_results',      [(Keys.R, Keys.MOD_SHIFT.value)])
        self.dump_textures =           Action(self, 'dump_textures',           [Keys.E]            )
        self.debug_toggle_flags =      Action(self, 'debug_toggle_flags',      [Keys.F]            )
        self.debug_e =                 Action(self, 'debug_e',                 [Keys.E]            )
        self.debug_f24 =               Action(self, 'debug_f24',               [Keys.F24]          )
        self.toggle_show_text =        Action(self, 'toggle_show_text',        [Keys.T]            )

        class ParallaxMap(SubKeyMap[tuple[()]]):
            def __init__(self, keymap: KeyMap):
                self.up =       Action(keymap, 'parallax_up',       [Keys.W], REQUIRED, context="parallax")
                self.down =     Action(keymap, 'parallax_down',     [Keys.S], REQUIRED, context="parallax")
                self.left =     Action(keymap, 'parallax_left',     [Keys.A], REQUIRED, context="parallax")
                self.right =    Action(keymap, 'parallax_right',    [Keys.D], REQUIRED, context="parallax")
                self.zoom_in =  Action(keymap, 'parallax_zoom_in',  [Keys.R], REQUIRED, context="parallax")
                self.zoom_out = Action(keymap, 'parallax_zoom_out', [Keys.F], REQUIRED, context="parallax")
                super().__init__()
        self.parallax = ParallaxMap(self)

        class FourKeyMap(SubKeyMap[tuple[bool, bool, bool, bool]]):
            def __init__(self, keymap: KeyMap):
                self.key1 = Action(keymap, 'fourkey_1', [Keys.D], REQUIRED | SINGLEBIND, context="fourkey")
                self.key2 = Action(keymap, 'fourkey_2', [Keys.F], REQUIRED | SINGLEBIND, context="fourkey")
                self.key3 = Action(keymap, 'fourkey_3', [Keys.J], REQUIRED | SINGLEBIND, context="fourkey")
                self.key4 = Action(keymap, 'fourkey_4', [Keys.K], REQUIRED | SINGLEBIND, context="fourkey")
                super().__init__(self.key1, self.key2, self.key3, self.key4)
        self.fourkey = FourKeyMap(self)

        class HeroMap(SubKeyMap[tuple[bool, bool, bool, bool, bool, bool, bool, bool]]):
            def __init__(self, keymap: KeyMap):
                self.green =     Action(keymap, 'hero_1',          [Keys.KEY_1, ControllerButtons.BOTTOM_FACE],  REQUIRED, context="hero")
                self.red =       Action(keymap, 'hero_2',          [Keys.KEY_2, ControllerButtons.RIGHT_FACE],  REQUIRED, context="hero")
                self.yellow =    Action(keymap, 'hero_3',          [Keys.KEY_3, ControllerButtons.TOP_FACE],  REQUIRED, context="hero")
                self.blue =      Action(keymap, 'hero_4',          [Keys.KEY_4, ControllerButtons.RIGHT_FACE],  REQUIRED, context="hero")
                self.orange =    Action(keymap, 'hero_5',          [Keys.KEY_5, ControllerButtons.LEFT_SHOULDER],  REQUIRED, context="hero")
                self.strumup =   Action(keymap, 'hero_strum_up',   [Keys.UP, ControllerButtons.DPAD_UP],     REQUIRED, context="hero")
                self.strumdown = Action(keymap, 'hero_strum_down', [Keys.DOWN, ControllerButtons.DPAD_DOWN],   REQUIRED, context="hero")
                self.power =     Action(keymap, 'hero_power',      [Keys.RSHIFT, ControllerButtons.BACK], REQUIRED, context="hero")
                super().__init__(self.green, self.red, self.yellow, self.blue, self.orange, self.strumup, self.strumdown, self.power)
        self.hero = HeroMap(self)

        class SongMenuMap(SubKeyMap[tuple[()]]):
            def __init__(self, keymap: KeyMap):
                self.min_factor_up =     Action(keymap, 'min_factor_up',     [Keys.Y],            REQUIRED, context="songmenu")
                self.min_factor_down =   Action(keymap, 'min_factor_down',   [Keys.H],            REQUIRED, context="songmenu")
                self.max_factor_up =     Action(keymap, 'max_factor_up',     [Keys.U],            REQUIRED, context="songmenu")
                self.max_factor_down =   Action(keymap, 'max_factor_down',   [Keys.J],            REQUIRED, context="songmenu")
                self.offset_up =         Action(keymap, 'offset_up',         [Keys.I],            REQUIRED, context="songmenu")
                self.offset_down =       Action(keymap, 'offset_down',       [Keys.K],            REQUIRED, context="songmenu")
                self.in_sin_up =         Action(keymap, 'in_sin_up',         [Keys.O],            REQUIRED, context="songmenu")
                self.in_sin_down =       Action(keymap, 'in_sin_down',       [Keys.L],            REQUIRED, context="songmenu")
                self.out_sin_up =        Action(keymap, 'out_sin_up',        [Keys.P],            REQUIRED, context="songmenu")
                self.out_sin_down =      Action(keymap, 'out_sin_down',      [Keys.SEMICOLON],    REQUIRED, context="songmenu")
                self.shift_up =          Action(keymap, 'shift_up',          [Keys.BRACKETLEFT],  REQUIRED, context="songmenu")
                self.shift_down =        Action(keymap, 'shift_down',        [Keys.APOSTROPHE],   REQUIRED, context="songmenu")
                self.move_forward_up =   Action(keymap, 'move_forward_up',   [Keys.BRACKETRIGHT], REQUIRED, context="songmenu")
                self.move_forward_down = Action(keymap, 'move_forward_down', [Keys.BACKSLASH],    REQUIRED, context="songmenu")
                self.y_shift_up =        Action(keymap, 'y_shift_up',        [Keys.COMMA],        REQUIRED, context="songmenu")
                self.y_shift_down =      Action(keymap, 'y_shift_down',      [Keys.PERIOD],       REQUIRED, context="songmenu")
                super().__init__()
        self.songmenu = SongMenuMap(self)

        self.set_defaults()

    def unbind(self, key: KeyMod | Button) -> None:
        """Unbind a particular key"""
        key = to_keymod(key)
        for action in self.get_actions(key):
            action.unbind(key)

    def unbind_all(self) -> None:
        """Unbind all actions."""
        for action in self.actions:
            action.unbind_all()

    def set_defaults(self) -> None:
        """Rebind all actions to their defaults."""
        for action in self.actions:
            action.set_defaults()

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        self.state.on_button_press(Keys(symbol), modifiers)

    def on_key_release(self, symbol: int, modifiers: int) -> None:
        self.state.on_button_release(Keys(symbol), modifiers)

    def on_button_press(self, controller: Controller, button_name: str) -> None:
        logger.info(f'Pressed controller button {button_name}')
        self.state.on_button_press(ControllerButtons(button_name), 0)

    def on_button_release(self, controller: Controller, button_name: str) -> None:
        self.state.on_button_release(ControllerButtons(button_name), 0)

    def on_stick_motion(self, controller: Controller, name: str, motion: Vec2) -> None:
        # TODO: Bug Dragon
        pass

    def on_dpad_motion(self, controller: Controller, motion: Vec2) -> None:
        dx, dy = motion - self.dpad
        if self.dpad.x != 0.0:
            # button released
            if dx > 0:
                self.state.on_button_release(ControllerButtons.DPAD_LEFT, 0)
            elif dx < 0:
                self.state.on_button_release(ControllerButtons.DPAD_RIGHT, 0)
        else:
            # button pressed
            if dx > 0:
                self.state.on_button_press(ControllerButtons.DPAD_RIGHT, 0)
            elif dx < 0:
                self.state.on_button_press(ControllerButtons.DPAD_LEFT, 0)

        if self.dpad.y != 0.0:
            # button released
            if dy > 0:
                self.state.on_button_release(ControllerButtons.DPAD_DOWN, 0)
            elif dy < 0:
                self.state.on_button_release(ControllerButtons.DPAD_UP, 0)
        else:
            # button pressed
            if dy > 0:
                self.state.on_button_press(ControllerButtons.DPAD_UP, 0)
            elif dy < 0:
                self.state.on_button_press(ControllerButtons.DPAD_DOWN, 0)
        self.dpad = motion

    def on_trigger_motion(self, controller: Controller, trigger_name: str, value: float) -> None:
        # TODO: Bug Dragon
        pass


    def to_json(self) -> KeyMapJson:
        return {action.id: action.to_json() for action in sorted(self.actions)}

    def set_from_json(self, data: KeyMapJson) -> None:
        for action in self.actions:
            action.set_from_json(data.get(action.id, ()))

    def save(self) -> None:
        charm.lib.data.save("keymap.json", self.to_json())

    def load(self) -> None:
        self.set_from_json(cast("KeyMapJson", charm.lib.data.load("keymap.json")))

    def get_actions(self, key: KeyMod | Button, context: Context | None = ALL) -> set[Action]:
        """Get all Actions mapped to a particular key"""
        key = to_keymod(key)
        if context == "global":
            context = ALL
        actions = self.keys[context].get(key, set())
        if context is not ALL:
            actions |= set(self.keys["global"].get(key, set()))
        return actions

    def __str__(self) -> str:
        return f"{[str(act) for act in self.actions]}"

    def add_action(self, action: Action) -> None:
        """INTERNAL"""
        self.actions.add(action)

    def add_key(self, key: KeyMod, action: Action, context: Context) -> None:
        """INTERNAL"""
        for ctx in (context, None):
            if key not in self.keys[ctx]:
                self.keys[ctx][key] = set()
            self.keys[ctx][key].add(action)

    def remove_key(self, key: KeyMod, action: Action, context: Context) -> None:
        """INTERNAL"""
        for ctx in (context, None):
            self.keys[ctx][key].discard(action)
            if len(self.keys[ctx][key]) == 0:
                del self.keys[ctx][key]

    def set_controller(self, idx: int = -1) -> None:
        controllers = get_controllers()
        if idx >= len(controllers):
            self.unbind_controller()
            return
        self.bind_controller(controllers[idx])

    def bind_controller(self, controller: Controller) -> None:
        if self.bound_controller != controller:
            self.unbind_controller()

        self.bound_controller = controller
        controller.open()
        controller.push_handlers(
            self.on_button_press,
            self.on_button_release,
            self.on_stick_motion,
            self.on_dpad_motion,
            self.on_trigger_motion
        )
        self.dpad: Vec2 = Vec2(controller.dpadx, controller.dpady)
        self.triggers: list[float] = [controller.lefttrigger, controller.righttrigger]
        self.l_stick: Vec2 = Vec2(controller.leftx, controller.lefty)
        self.r_stick: Vec2 = Vec2(controller.rightx, controller.righty)
        logger.info(f'Bound Controller {controller}')

    def unbind_controller(self) -> None:
        if not self.bound_controller:
            return
        logger.info(f'Unbound Controller {self.bound_controller}')

        self.bound_controller.remove_handlers(
            self.on_button_press,
            self.on_button_release,
            self.on_stick_motion,
            self.on_dpad_motion,
            self.on_trigger_motion
        )
        self.bound_controller.close()
        self.bound_controller = None  # type: ignore -- wah wah wah type hinting
        self.dpad = Vec2()
        self.triggers = [0.0, 0.0]
        self.l_stick = Vec2()
        self.r_stick = Vec2()

keymap = KeyMap()
