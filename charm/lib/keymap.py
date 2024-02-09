from typing import Optional, Union
import arcade.key
from arcade.key import RETURN, ENTER, ESCAPE, BACKSPACE, D, F, J, K, KEY_7, GRAVE, \
    KEY_1, KEY_2, KEY_3, KEY_4, KEY_5, UP, DOWN, RSHIFT, SPACE, F11, M
from charm.lib.utils import findone
from charm.lib.errors import MultipleKeyBindsError, ExclusiveKeyBindError, \
    KeyUnboundError, ActionNameConflictError, ActionNotFoundError, SameInputMultipleError, \
    SetNotFoundError, KeyNotFoundInActionError, KeyUnrecognizedError, ActionNotInSetError

Key = int
Keys = list[int]


def get_arcade_key_name(i: Key) -> str:
    it = (k for k, v in arcade.key.__dict__.items() if v == i)
    found = findone(it)
    if found is None:
        raise KeyUnrecognizedError(i)
    return found


class Action:
    def __init__(self, name: str, inputs: Keys = None, required = False, allow_multiple = False, exclusive = False) -> None:
        self.name = name
        self.default: Keys = inputs
        self.inputs: Keys = [] if inputs is None else inputs
        self.required = required
        self.allow_multiple: bool = allow_multiple
        self.exclusive: bool = exclusive

        self.state = False

    def __eq__(self, other: Union[Key, 'Action']) -> bool:
        return other in self.inputs if isinstance(other, Key) else (self.name, self.inputs) == (other.name, other.inputs)

    def __str__(self) -> str:
        return f"{self.name}{'*' if self.exclusive else ''}: {[get_arcade_key_name(i) for i in self.inputs]}{'*' if self.allow_multiple else ''} [{'X' if self.state else '_'}]"


class ActionSet:
    def __init__(self, d: dict[str, Action]):
        self._dict: dict[str, Action] = d

    @property
    def state(self) -> tuple[bool]:
        return tuple([a.state for a in self._dict.values()])

    def __getattr__(self, name: str) -> Action:
        if name not in self._dict:
            raise ActionNotInSetError(name)
        return self._dict[name]

    def __iter__(self):
        return (getattr(self, name) for name in self._dict.keys())


class KeyMap:
    def __init__(self):
        """Access and set mappings for inputs to actions. Key binding."""
        self.actions: list[Action] = [
            Action('start', [RETURN, ENTER], True, True, True),
            Action('back', [ESCAPE, BACKSPACE], True, True, True),
            Action('debug', [GRAVE, KEY_7], False, True, True),
            Action('pause', [SPACE], True, False, True),
            Action('fullscreen', [F11], True, False, True),
            Action('mute', [M], True, False, True),
            Action('fourkey_1', [D], False, False, False),
            Action('fourkey_2', [F], False, False, False),
            Action('fourkey_3', [J], False, False, False),
            Action('fourkey_4', [K], False, False, False),
            Action('hero_1', [KEY_1], False, False, False),
            Action('hero_2', [KEY_2], False, False, False),
            Action('hero_3', [KEY_3], False, False, False),
            Action('hero_4', [KEY_4], False, False, False),
            Action('hero_5', [KEY_5], False, False, False),
            Action('hero_strum_up', [UP], False, False, False),
            Action('hero_strum_down', [DOWN], False, False, False),
            Action('hero_power', [RSHIFT], False, False, False)
        ]

        # Make sure there's no duplicate action names since they're basically keys.
        seen = set()
        dupes = [x for x in [a.name for a in self.actions] if x in seen or seen.add(x)]
        for d in dupes:
            raise ActionNameConflictError(d)

        # Create action sets (hardcoded, frozen.)
        self.sets: dict[str, ActionSet] = {
            "fourkey": ActionSet({
                "key1": self.fourkey_1,
                "key2": self.fourkey_2,
                "key3": self.fourkey_3,
                "key4": self.fourkey_4
            }),
            "hero": ActionSet({
                "green": self.hero_1,
                "red": self.hero_2,
                "yellow": self.hero_3,
                "blue": self.hero_4,
                "orange": self.hero_5,
                "strumup": self.hero_strum_up,
                "strumdown": self.hero_strum_down,
                "power": self.hero_power
            })
        }

    def __getattr__(self, item: str) -> Optional[Action]:
        """Get an action by name."""
        return findone((a for a in self.actions if a.name == item))

    def get_set(self, name: str) -> ActionSet:
        """Get an action set by name."""
        s = self.sets.get(name, None)
        if s is None:
            raise SetNotFoundError(name)
        return s

    def bind_key(self, name: str, key: Key):
        """Set `key` as a valid input for the '`name`' action."""
        action = self[name]
        key_string = get_arcade_key_name(key)
        if action is None:
            raise ActionNotFoundError(name)
        if key in action.inputs:
            raise SameInputMultipleError(name, key_string)
        for a in self.actions:
            if a.exclusive and key in a.inputs:
                raise ExclusiveKeyBindError(key_string, [a.name, name])
        action.inputs.append(key)
        if not action.allow_multiple and len(action.inputs) >= 1:
            raise MultipleKeyBindsError(name)

    def replace_key(self, name: str, old_key: Key, new_key: Key):
        """Replace the input `old_key` with `new_key` in the '`name`' action."""
        action = self[name]
        old_key_string = get_arcade_key_name(old_key)
        new_key_string = get_arcade_key_name(new_key)
        if action is None:
            raise ActionNotFoundError(name)
        if old_key not in action.inputs:
            raise KeyNotFoundInActionError(name, old_key_string)
        if new_key in action.inputs:
            raise SameInputMultipleError(name, new_key_string)
        for a in self.actions:
            if a.exclusive and new_key in a.inputs:
                raise ExclusiveKeyBindError(new_key_string, [a.name, name])
        self.actions.remove(old_key)
        self.actions.append(new_key)

    def clear_keys(self, name: str):
        """Remove all inputs from the '`name`' action."""
        action = self[name]
        if action is None:
            raise ActionNotFoundError(name)
        action.inputs = []

    def set_defaults(self, name: str):
        """Set the '`name`' action's inputs to its default state."""
        action = self[name]
        if action is None:
            raise ActionNotFoundError(name)
        action.inputs = action.default.copy()

    def set_all_defaults(self):
        """Set all actions inputs to their default state."""
        for action in self.actions:
            self.set_defaults(action.name)

    def validate(self, name: str) -> bool:
        """Check the action for errors."""
        action = self[name]
        # Action not found
        if action is None:
            raise ActionNotFoundError(name)
        # Action doesn't allow multiple binds, but there are
        if not action.allow_multiple and len(action.inputs) > 1:
            raise MultipleKeyBindsError(name)
        # Unbound
        if action.required and not action.inputs:
            raise KeyUnboundError(name)
        # Exclusive key found on multiple actions
        for a in self.actions:
            for key in action.inputs:
                key_string = get_arcade_key_name(key)
                if a.exclusive and key in a.inputs:
                    raise ExclusiveKeyBindError(key_string, [a.name, name])
        return True

    def validate_all(self) -> bool:
        """Check all actions for errors."""
        for action in self.actions:
            self.validate(action.name)
        return True

    def set_state(self, key: Key, state: bool):
        for action in [a for a in self.actions if a == key]:
            action.state = state

    def __str__(self) -> str:
        return f"{[str(i) for i in self.actions]}"


keymap = None


def get_keymap() -> KeyMap:
    global keymap
    if keymap is not None:
        return keymap
    keymap = KeyMap()
    return keymap


def set_keymap(new_keymap: KeyMap):
    global keymap
    keymap = new_keymap
