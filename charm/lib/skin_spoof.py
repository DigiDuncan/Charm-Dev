from typing import Protocol, Any


class FNFTexturesTypes(Protocol):
    up_arrow: float
    down_arrow: float


class SkinSetter:

    def __init__(self, source: dict[str, Any]):
        self._data: dict = source

    def __getattr__(self, item: str):
        return self._data[item]


fnf_textures: FNFTexturesTypes = SkinSetter({'up_arrow': 1.0, "down_arrow": 1.0}) # type: ignore[reportAssignmentType]

class ModeEngine(Protocol):
    pass

class ModeLayout(Protocol):
    pass


# class GameMode(TypedDict):
#     engine: type[ModeEngine]
#     layout: type[ModeLayout]

# GAME_MODES: dict[str, GameMode] = {
#     'fnf': {'engine': ModeEngine, 'layout': ModeLayout}
# }
