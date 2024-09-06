import logging
from math import ceil

from arcade import Text, Sound, color as colors

from charm.lib import paths

from charm.lib.charm import GumWrapper
from charm.lib.digiview import DigiView, disable_when_focus_lost, shows_errors
from charm.lib.errors import NoChartsError
from charm.lib.gamemodes.four_key import FourKeyEngine
from charm.lib.gamemodes.taiko import TaikoHighway, TaikoSong
from charm.lib.keymap import keymap
from charm.lib.logsection import LogSection
from charm.lib.oggsound import OGGSound
from charm.lib.trackcollection import TrackCollection
from charm.unused.results import ResultsView

logger = logging.getLogger("charm")


class TaikoSongTestView(DigiView):
    def __init__(self, back: DigiView):
        super().__init__(fade_in=1, back=back)
        self.name = "Freedom Dive"
        self.song_path = paths.songspath / "taiko" / self.name
        self.tracks: TrackCollection = None
        self.highway: TaikoHighway = None
        self.engine: FourKeyEngine = None
        self.countdown: float = 3
        self.countdown_over = False

    @shows_errors
    def setup(self) -> None:
        super().presetup()

        with LogSection(logger, "loading audio"):
            audio_paths = [a for a in self.song_path.glob("*.mp3")] + [a for a in self.song_path.glob("*.wav")] + [a for a in self.song_path.glob("*.ogg")]
            trackfiles = []
            for s in audio_paths:
                trackfiles.append(OGGSound(s) if s.suffix == ".ogg" else Sound(s))
            self.tracks = TrackCollection([Sound(s) for s in audio_paths])

        with LogSection(logger, "loading song data"):
            self.taiko_song = TaikoSong.parse(self.song_path)
            self.chart = self.taiko_song.charts[0]
            if self.chart is None:
                raise NoChartsError(self.taiko_song.metadata.title)

        with LogSection(logger, "loading highway"):
            self.highway = TaikoHighway(self.chart, (0, self.window.height / 2), (self.window.width, 100), auto = True)

        self.text = Text("[LOADING]", -5, self.window.height - 5, color = colors.BLACK, font_size = 24, align = "right", anchor_y="top", font_name = "bananaslip plus", width = self.window.width, multiline = True)
        self.countdown_text = Text("0", self.window.width / 2, self.window.height / 2, colors.BLACK, 72, align="center", anchor_x="center", anchor_y="center", font_name = "bananaslip plus", width = 100)

        self.window.presence.set("Playing Taiko")

        # Generate "gum wrapper" background
        self.gum_wrapper = GumWrapper()
        self.success = True

        super().postsetup()

    @shows_errors
    def on_show_view(self) -> None:
        self.window.theme_song.volume = 0
        if self.success is False:
            self.window.show_view(self.back)
            self.window.theme_song.volume = 0.25
        self.countdown = 4
        super().on_show_view()

    @shows_errors
    def on_key_something(self, symbol: int, modifiers: int, press: bool) -> None:
        pass

    def generate_data_string(self) -> str:
        return (f"Time: {int(self.tracks.time // 60)}:{int(self.tracks.time % 60):02}")

    @shows_errors
    @disable_when_focus_lost(keyboard=True)
    def on_key_press(self, symbol: int, modifiers: int) -> None:
        super().on_key_press(symbol, modifiers)
        if keymap.back.pressed:
            self.go_back()
        elif keymap.pause.pressed:
            if self.countdown <= 0:
                self.tracks.pause() if self.tracks.playing else self.tracks.play()
        elif keymap.seek_zero.pressed:
            self.tracks.seek(0)
        elif keymap.seek_backward.pressed:
            self.tracks.seek(self.tracks.time - 5)
        elif keymap.seek_forward.pressed:
            self.tracks.seek(self.tracks.time + 5)
        elif self.window.debug.enabled and keymap.debug_toggle_hit_window:
            self.highway.show_hit_window = not self.highway.show_hit_window
        elif self.window.debug.enabled and keymap.debug_show_results:
            self.show_results()
        self.on_key_something(symbol, modifiers, True)

    @shows_errors
    def on_key_release(self, symbol: int, modifiers: int) -> None:
        super().on_key_release(symbol, modifiers)
        self.on_key_something(symbol, modifiers, False)

    def go_back(self) -> None:
        self.tracks.close()
        super().go_back()

    def show_results(self) -> None:
        self.tracks.close()
        results_view = ResultsView(back=self.back, results=self.engine.generate_results())
        results_view.setup()
        self.window.show_view(results_view)

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(height, width)
        self.highway.pos = (0, 0)
        self.highway.y += self.window.height // 2 - self.highway.h // 2  # center the highway
        self.text.position = (-5, self.window.height - 5)
        self.countdown_text.position = (self.window.width / 2, self.window.height / 2)

    @shows_errors
    def on_update(self, delta_time) -> None:
        super().on_update(delta_time)

        if not self.tracks.loaded:
            return

        self.highway.update(0 - self.countdown if not self.countdown_over else self.tracks.time)

        data_string = self.generate_data_string()
        if self.text.text != data_string:
            self.text.text = data_string

        if self.countdown > 0:
            self.countdown -= delta_time
            if self.countdown < 0:
                self.countdown = 0
            self.countdown_text.text = str(ceil(self.countdown))

        if self.countdown <= 0 and not self.countdown_over:
            self.tracks.play()
            self.countdown_over = True

        if self.tracks.time >= self.tracks.duration:
            self.show_results()

        self.gum_wrapper.on_update(delta_time)

    @shows_errors
    def on_draw(self) -> None:
        super().predraw()
        # Charm BG
        self.gum_wrapper.draw()

        self.highway.draw()

        self.text.draw()

        if self.countdown > 0:
            self.countdown_text.draw()
        super().postdraw()
