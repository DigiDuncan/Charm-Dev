from typing import Optional, Union
import arcade.key
from arcade.key import D, F, J, K

class ActionNameConflictError(Exception):
    pass

class SetNotFoundError(Exception):
    pass

class KeyUnrecognizedError(Exception):
    pass

class ActionNotInSetError(Exception):
    pass


Key = int
Keys = list[int]

def findone(iterator):
    try:
        val = next(iterator)
    except StopIteration:
        val = None
    return val


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
    # Singleton BS
    def __new__(cls):
        if not hasattr(cls, '_instance'):
            cls._instance = super(KeyMap, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Access and set mappings for inputs to actions. Key binding."""
        self.actions: list[Action] = [
            Action('fourkey_1', [D], False, False, False),
            Action('fourkey_2', [F], False, False, False),
            Action('fourkey_3', [J], False, False, False),
            Action('fourkey_4', [K], False, False, False)
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

    def __str__(self) -> str:
        return f"{[str(i) for i in self.actions]}"


def test():
    four_key0 = KeyMap().get_set("fourkey")
    print(four_key0.state)

    # The D key has been hit...
    four_key1 = KeyMap().get_set("fourkey")
    for key in four_key1:
        if key == D:
            key.state = True
            print(f"Set {key} state to True")

    # Let's see what the state is now
    four_key2 = KeyMap().get_set("fourkey")
    print(four_key2.state)


if __name__ == "__main__":
    test()
