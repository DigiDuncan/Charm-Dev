from typing import TypedDict

from charm.core.generic.engine import Engine, AutoEngine
from charm.core.generic.display import Display

# -- ENGINES --
from charm.core.gamemodes.fnf.engine import FNFEngine
from charm.core.gamemodes.four_key.engine import FourKeyEngine
from charm.core.gamemodes.hero.engine import HeroEngine
from charm.core.gamemodes.taiko.engine import TaikoEngine

# -- DISPLAYS --
from charm.core.gamemodes.fnf.display import FNFDisplay
from charm.core.gamemodes.four_key.display import FourKeyDisplay
from charm.core.gamemodes.hero.display import HeroDisplay
from charm.core.gamemodes.taiko.display import TaikoDisplay


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
