from __future__ import annotations
import logging

from charm.lib.charm import GumWrapper
from charm.lib.digiview import DigiView, shows_errors, disable_when_focus_lost
from charm.views.results import ResultsView
from charm.lib.keymap import keymap

from charm.lib.gamemodes import GameModeDefinition, GAMEMODES, Engine, Display, Chart
from charm.lib.trackcollection import TrackCollection
from charm.lib.settings import settings

# -- TEMP --
from charm.lib.songloader import load_songs_fnf
from charm.lib.gamemodes.fnf import FNFSong
from random import choice

logger = logging.getLogger("charm")


class GameView(DigiView):
    def __init__(self, back: DigiView):
        super().__init__(fade_in=1, back=back)
        self._initialised: bool = False
        self._mode_definition: GameModeDefinition = None  # type: ignore[]
        self._tracks: TrackCollection = None  # type: ignore[]
        self._engine: Engine = None  # type: ignore[]
        self._display: Display = None  # type: ignore[]
        self._paused: bool = True

    @property
    def paused(self) -> bool:
        return self._paused

    @shows_errors
    def pause(self, *, force: bool = False) -> None:
        if self._paused and not force:
            return
        self._paused = True
        self._engine.pause()
        self._display.pause()
        self._tracks.pause()

    @shows_errors
    def unpause(self, *, force: bool = False) -> None:
        if not self._paused and not force:
            return
        self._paused = False
        self._engine.unpause()
        self._display.unpause()
        self._tracks.volume = settings.get_volume('music')
        self._tracks.play()

    @shows_errors
    def initialise_gamemode(self, gamemode: str, tracks: TrackCollection, charts: tuple[Chart, ...]) -> None:
        self._mode_definition = GAMEMODES[gamemode]

        self._tracks = tracks

        self._engine = self._mode_definition['engines'](charts[0])
        self._display = self._mode_definition['display'](self.window, self._engine, charts)

    @shows_errors
    def setup(self) -> None:
        self.presetup()
        self.gum_wrapper = GumWrapper()

        # TODO: make this not be how it works

        song = choice(load_songs_fnf())
        path = song.path

        tracks = TrackCollection.from_path(path)
        fnf_song = FNFSong.parse(path)

        self.initialise_gamemode(song.gamemode, tracks, tuple(fnf_song.charts))
        self.postsetup()

    def on_show_view(self) -> None:
        self.window.theme_song.volume = 0
        self.unpause(force=True)

    def go_back(self):
        self._tracks.close()
        super().go_back()

    @shows_errors
    @disable_when_focus_lost(keyboard=True)
    def on_key_press(self, symbol: int, modifiers: int) -> None:
        super().on_key_press(symbol, modifiers)
        if keymap.back.pressed:
            self.go_back()
        elif keymap.pause.pressed:
            self.unpause() if self.paused else self.pause()
        elif keymap.seek_backward.pressed:
            self._tracks.seek(self._tracks.time - 5)
        elif keymap.seek_forward.pressed:
            self._tracks.seek(self._tracks.time + 5)
        elif keymap.log_sync.pressed:
            self._tracks.log_sync()
        elif keymap.toggle_distractions.pressed:
            pass
            # TODO: self.distractions = not self.distractions
        elif keymap.toggle_chroma.pressed:
            pass
            # TODO: self.chroma_key = not self.chroma_key
        elif self.window.debug.enabled and keymap.debug_toggle_hit_window.pressed:
            pass
            # TODO: self.highway_1.show_hit_window = not self.highway_1.show_hit_window
        elif self.window.debug.enabled and keymap.debug_show_results.pressed:
            self.show_results()

        if not self._paused:
            self._engine.on_key_press(symbol, modifiers)

    @shows_errors
    @disable_when_focus_lost(keyboard=True)
    def on_key_release(self, symbol: int, modifiers: int) -> None:
        super().on_key_release(symbol, modifiers)
        if not self._paused:
            self._engine.on_key_release(symbol, modifiers)

    @shows_errors
    def on_update(self, delta_time: float) -> None:
        super().on_update(delta_time)
        self.gum_wrapper.on_update(delta_time)

        self._engine.update(self._tracks.time)
        self._engine.calculate_score()

        if self._tracks.time >= self._tracks.duration:
            self.show_results()

        self._display.update(self._tracks.time)

    @shows_errors
    def on_draw(self) -> None:
        self.predraw()
        # Charm BG
        self.gum_wrapper.draw()
        self._display.draw()
        self.postdraw()

    def show_results(self) -> None:
        self._tracks.close()
        results_view = ResultsView(back=self.back, results=self._engine.generate_results())
        results_view.setup()
        self.window.show_view(results_view)
