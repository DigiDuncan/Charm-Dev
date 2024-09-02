from typing import TypedDict

from charm.refactor.generic.engine import Engine, AutoEngine
from charm.refactor.generic.display import Display

# -- ENGINES --
from charm.refactor.engines.fnf import FNFEngine
from charm.refactor.engines.four_key import FourKeyEngine
from charm.refactor.engines.hero import HeroEngine
from charm.refactor.engines.taiko import TaikoEngine

# -- DISPLAYS --
from charm.refactor.displays.fnf import FNFDisplay
from charm.refactor.displays.four_key import FourKeyDisplay
from charm.refactor.displays.hero import HeroDisplay
from charm.refactor.displays.taiko import TaikoDisplay


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
