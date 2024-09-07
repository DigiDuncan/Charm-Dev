from typing import TypedDict

from charm.core.generic import Engine, Display, Chart

# -- fnf --
from charm.core.gamemodes.fnf import FNFEngine, FNFDisplay

__all__ = (
    'GameModeDefinition',
    'GAMEMODES',
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
