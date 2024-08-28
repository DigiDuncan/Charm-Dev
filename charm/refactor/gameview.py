from charm.lib.digiview import DigiView, shows_errors, disable_when_focus_lost

from charm.lib.charm import GumWrapper
from charm.refactor.results import ResultsView
from charm.lib.keymap import keymap

from charm.refactor.generic.display import Display
from charm.refactor.generic.engine import Engine

from charm.refactor.generic.chartset import ChartSet
from charm.refactor.generic.chart import Chart

from charm.refactor.gamemodes import GAMEMODES
from charm.lib.trackcollection import TrackCollection
from charm.lib.settings import settings

class GameView(DigiView):

    def __init__(self, *, back: DigiView | None = None, fade_in: float = 0):
        super().__init__(back=back, fade_in=fade_in)
        self._initialized: bool = False

        self._tracks: TrackCollection = None  # type: ignore[]

        self._chartset: ChartSet = None  # type: ignore[]
        self._charts: list[Chart] = None  # type: ignore[]

        self._engine: Engine = None  # type: ignore[]
        self._display: Display = None  # type: ignore[]

        self._paused = False

    @shows_errors
    def initialize_chart(self, chartset: ChartSet, charts: list[Chart]) -> None:
        self._chartset = chartset
        self._charts = charts

        self._paused = True

    @shows_errors
    def setup(self) -> None:
        self.presetup()
        self.gum_wrapper = GumWrapper()

        if self._charts is None or not self._charts or self._chartset is None:
            # TODO: make an explicit error for this
            raise ValueError("The GameView has not been initialised with a Chartset or Chart")

        primary_chart, *other_charts = self._charts

        gamemode_definitions = GAMEMODES[primary_chart.metadata.gamemode]

        self._tracks = TrackCollection.from_path(self._chartset.metadata.path)

        self._engine = gamemode_definitions['engines'](primary_chart)
        self._display = gamemode_definitions['display'](self._engine, tuple(self._charts))

        # HACK: Wow, don't do this! Display doesn't get the TrackCollection so we need to solve this somehow
        if hasattr(self._display, "timer"):
            self._display.timer.total_time = self._tracks.duration

        self._paused = False
        self._initialized = True

        self.postsetup()

    def on_show_view(self) -> None:
        super().on_show_view()
        self.window.theme_song.volume = 0
        self.unpause(force=True)

    def go_back(self) -> None:
        self._tracks.close()
        super().go_back()

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
    @disable_when_focus_lost(keyboard=True)
    def on_key_press(self, symbol: int, modifiers: int) -> None:
        super().on_key_press(symbol, modifiers)
        if keymap.back.pressed:
            self.go_back()
        elif keymap.pause.pressed:
            self.unpause() if self.paused else self.pause()
        elif keymap.seek_backward.pressed:
            return
            # TODO
            self._tracks.seek(self._tracks.time - 5)
        elif keymap.seek_forward.pressed:
            return
            # TODO
            self._tracks.seek(self._tracks.time + 5)
        elif keymap.log_sync.pressed:
            return
            # TODO
            self._tracks.log_sync()
        elif self.window.debug.enabled and keymap.debug_toggle_hit_window.pressed:
            return
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
        # TODO: Refactor to use new types
        results_view = ResultsView(back=self.back, results=self._engine.generate_results())
        results_view.setup()
        self.window.show_view(results_view)

