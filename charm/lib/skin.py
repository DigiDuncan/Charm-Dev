from __future__ import annotations

from copy import copy
from pathlib import Path
from typing import Any, TypeVar, cast

from arcade import Sprite, Texture
from addict import Addict

from charm.lib.utils import img_from_path

AbsolutePoint = tuple[int, int]
RelativePoint = tuple[float, float]
Color = tuple[int, int, int, int]

T = TypeVar('T')

class SkinItem:
    def __init__(self, key: str, default: T, value: T | None = None):
        self.key = key
        self.default = default

        self._value = value if value else copy(default)

    @property
    def value(self) -> T:
        return self._value if self._value is not None else self.default

    @value.setter
    def value(self, v: T):
        self._value = v


class SkinBool(SkinItem):
    def __init__(self, key: str, default: bool, value: bool | None):
        super().__init__(key, default, value)
        self.default = default
        self._value = value

    @property
    def value(self) -> bool:
        return self._value if self._value is not None else self.default

    @value.setter
    def value(self, v: bool):
        self._value = v


class SkinInt(SkinItem):
    def __init__(self, key: str, default: int, value: int | None):
        super().__init__(key, default, value)
        self.default = default
        self._value = value

    @property
    def value(self) -> int:
        return self._value if self._value is not None else self.default

    @value.setter
    def value(self, v: int):
        self._value = v


class SkinFloat(SkinItem):
    def __init__(self, key: str, default: float, value: float | None):
        super().__init__(key, default, value)
        self.default = default
        self._value = value

    @property
    def value(self) -> float:
        return self._value if self._value is not None else self.default

    @value.setter
    def value(self, v: float):
        self._value = v


class SkinAbsolutePoint(SkinItem):
    def __init__(self, key: str, default: AbsolutePoint, value: AbsolutePoint | None):
        super().__init__(key, default, value)
        self.default = default
        self._value = value

    @property
    def value(self) -> AbsolutePoint:
        return self._value if self._value is not None else self.default

    @value.setter
    def value(self, v: AbsolutePoint):
        self._value = v

    @property
    def x(self) -> int:
        return self.value[0]

    @x.setter
    def x(self, val: int):
        self.value = (val, self.y)

    @property
    def y(self) -> int:
        return self.value[1]

    @y.setter
    def y(self, val: int):
        self.value = (self.x, val)


class SkinRelativePoint(SkinItem):
    def __init__(self, key: str, default: RelativePoint, value: RelativePoint | None):
        super().__init__(key, default, value)
        self.default = default
        self._value = value

    @property
    def value(self) -> RelativePoint:
        return self._value if self._value is not None else self.default

    @value.setter
    def value(self, v: RelativePoint):
        self._value = v

    @property
    def x(self) -> float:
        return self.value[0]

    @x.setter
    def x(self, val: float):
        self.value = (val, self.y)

    @property
    def y(self) -> float:
        return self.value[1]

    @y.setter
    def y(self, val: float):
        self.value = (self.x, val)

    def absolute(self, window_size: AbsolutePoint) -> AbsolutePoint:
        return AbsolutePoint(self.x * window_size[0], self.y * window_size[1])


class SkinColor(SkinItem):
    def __init__(self, key: str, default: Color, value: Color | None):
        super().__init__(key, default, value)
        self.default = default
        self._value = value

    @property
    def value(self) -> Color:
        return self._value if self._value is not None else self.default

    @value.setter
    def value(self, v: Color):
        self._value = v

    @property
    def r(self) -> int:
        return self.value[0]

    @r.setter
    def r(self, val: int):
        self.value = (val, self.g, self.b, self.a)

    @property
    def g(self) -> int:
        return self.value[1]

    @g.setter
    def g(self, val: int):
        self.value = (self.r, val, self.b, self.a)

    @property
    def b(self) -> int:
        return self.value[2]

    @b.setter
    def b(self, val: int):
        self.value = (self.r, self.g, val, self.a)

    @property
    def a(self) -> int:
        return self.value[3]

    @a.setter
    def a(self, val: int):
        self.value = (self.r, self.g, self.b, val)


class SkinSprite(SkinItem):
    def __init__(self, key: str, default: str, value: str | None):
        super().__init__(key, default, value)
        self.default = default
        self._value = value

    @property
    def value(self) -> str:
        return self._value if self._value is not None else self.default

    @value.setter
    def value(self, v: str):
        self._value = v

    def get_path_from_root(self, root: Path) -> Path:
        path_components = self.value.split(".")
        path = root
        for p in path_components:
            path = path / p
        return path

    def get_texture(self, root: Path) -> Texture:
        path = self.get_path_from_root(root)
        image = img_from_path(path)
        return Texture(image)

    def get_sprite(self, root: Path) -> Sprite:
        return Sprite(self.get_path_from_root(root))

class Skin:
    def __init__(self, root: Path):
        self.root = root
        self.data = Addict()

    def get_asset(self, item_key: str) -> Any:
        skin_item = next((s for s in self.skin_items if s.key == item_key))
        if isinstance(skin_item, SkinSprite):
            return skin_item.get_sprite(self.root)
        else:
            return skin_item.value

    def __getattribute__(self, name: str) -> Any:
        return self.get_asset(name)

    @classmethod
    def from_toml(cls, t: dict) -> Skin:
        pass
