from typing import TypedDict

from charm.refactor.generic.engine import Engine
from charm.refactor.generic.display import Display

# -- ENGINES --
from charm.refactor.engines.fnf import FNFEngine

# -- DISPLAYS --
from charm.refactor.displays.fnf import FNFDisplay


# ?: Add other gamemode properties?
# !: We are doing a single engine per mode, prevents multiplayer, but lets leave that for after MVP
class GameModeDefinition(TypedDict):
    engines: type[Engine]
    display: type[Display]


GAMEMODES: dict[str, GameModeDefinition] = {
    'fnf': GameModeDefinition(engines=FNFEngine, display=FNFDisplay)
}
