from typing import TypedDict

from charm.core.generic import Engine, AutoEngine, Display

# -- ENGINES & DISPLAYS --
from charm.core.gamemodes.fnf import FNFEngine, FNFDisplay
from charm.core.gamemodes.four_key import FourKeyEngine, FourKeyDisplay
from charm.core.gamemodes.hero import HeroEngine, HeroDisplay
from charm.core.gamemodes.taiko import TaikoEngine, TaikoDisplay


# ?: Add other gamemode properties?
# !: We are doing a single engine per mode, prevents multiplayer, but lets leave that for after MVP
class GameModeDefinition(TypedDict):
    engines: type[Engine]
    display: type[Display]


GAMEMODES: dict[str, GameModeDefinition] = {
    'fnf': GameModeDefinition(engines=FNFEngine, display=FNFDisplay), # TODO: Doesn't work with Auto Engine
    '4k': GameModeDefinition(engines=FourKeyEngine, display=FourKeyDisplay),
    'hero': GameModeDefinition(engines=AutoEngine, display=HeroDisplay),
    'taiko': GameModeDefinition(engines=AutoEngine, display=TaikoDisplay)
}