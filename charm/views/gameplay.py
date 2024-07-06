from __future__ import annotations
import logging

from charm.lib.charm import GumWrapper
from charm.lib.digiview import DigiView, shows_errors, disable_when_focus_lost
from charm.lib.keymap import keymap

from charm.lib.gamemodes import GameModeDefinition, GAMEMODES, Engine, Display, Chart
from charm.lib.oggsound import OGGSound
from charm.lib.trackcollection import TrackCollection

logger = logging.getLogger("charm")


class GameView(DigiView):
    def __init__(self, back: DigiView):
        super().__init__(fade_in=1, back=back)
        self._mode_definition: GameModeDefinition = None  # type: ignore[]
        self._song_source: OGGSound = None  # type: ignore[]
        self._song: TrackCollection = None  # type: ignore[]
        self._engine: Engine = None  # type: ignore[]
        self._display: Display = None  # type: ignore[]

    @shows_errors
    def initialise_gamemode(self, gamemode: str, song: OGGSound, charts: tuple[Chart, ...]) -> None:
        self._mode_definition = GAMEMODES[gamemode]

        self._song_source = song

        self._engine = self._mode_definition['engines'](charts[0])
        self._display = self._mode_definition['display'](self._engine)

        self.components.register(self._engine)
        self.components.register(self._display)

    @shows_errors
    def setup(self) -> None:
        self.presetup()
        self.gum_wrapper = GumWrapper()
        self.postsetup()

    def on_show_view(self) -> None:
        self.window.theme_song.volume = 0

    @shows_errors
    @disable_when_focus_lost(keyboard=True)
    def on_key_press(self, symbol: int, modifiers: int) -> None:
        super().on_key_press(symbol, modifiers)
        if keymap.back.pressed:
            self.go_back()

    @shows_errors
    def on_update(self, delta_time: float) -> None:
        super().on_update(delta_time)
        self.gum_wrapper.on_update(delta_time)
        self._engine.update(self._song.time)
        self._display.update(delta_time)

    @shows_errors
    def on_draw(self) -> None:
        self.predraw()
        # Charm BG
        self.gum_wrapper.draw()
        self._display.draw()
        self.postdraw()
