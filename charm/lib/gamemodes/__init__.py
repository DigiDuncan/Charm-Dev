from typing import TypedDict

from charm.lib.generic.engine import Engine
from charm.lib.generic.display import Display
from charm.lib.generic.song import Song, Chart

# -- fnf --
from charm.lib.gamemodes.fnf import FNFEngine, FNFDisplay

__all__ = (
    'GameModeDefinition',
    'GAMEMODES',
    'Song',
    'Chart',
    'Engine',
    'Display'
)


# ?: Add other gamemode properties?
# !: We are doing a single engine per mode, prevents multiplayer, but lets leave that for after MVP
class GameModeDefinition(TypedDict):
    engines: type[Engine]
    display: type[Display]


GAMEMODES: dict[str, GameModeDefinition] = {
    'fnf': GameModeDefinition(engines=FNFEngine, display=FNFDisplay)
}
