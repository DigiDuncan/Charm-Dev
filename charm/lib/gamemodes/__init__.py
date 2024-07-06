from typing import TypedDict

from charm.lib.generic.engine import Engine
from charm.lib.generic.display import Display
from charm.lib.generic.song import Song, Chart


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
    song: type[Song[Chart]]  # !: So uh we are redoing charts soon so this won't work
    engines: type[Engine]
    display: type[Display]


GAMEMODES: dict[str, GameModeDefinition] = {

}
