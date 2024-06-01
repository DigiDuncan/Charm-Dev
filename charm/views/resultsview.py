import importlib.resources as pkg_resources
import logging

import arcade

from charm.lib.charm import CharmColors, generate_gum_wrapper, move_gum_wrapper
from charm.lib.digiview import DigiView, ignore_imgui, shows_errors
from charm.lib.generic.results import Results, Heatmap
from charm.lib import paths

import charm.data.audio
import charm.data.images.skins
from charm.lib.keymap import get_keymap
from charm.lib.scores import ScoreDB
from charm.lib.settings import settings

logger = logging.getLogger("charm")


class ResultsView(DigiView):
    def __init__(self, results: Results, back: DigiView):
        super().__init__(fade_in=1, bg_color=CharmColors.FADED_GREEN, back=back)
        self.song = None
        self.results = results

    @shows_errors
    def setup(self) -> None:
        super().setup()

        with pkg_resources.path(charm.data.audio, "music-results.mp3") as p:
            self._song = arcade.Sound(p)

        with pkg_resources.path(charm.data.images.skins.base, f"grade-{self.results.grade}.png") as p:
            self.grade_sprite = arcade.Sprite(p)
        self.grade_sprite.bottom = 25
        self.grade_sprite.left = 25

        self.score_text = arcade.Text(f"{self.results.score}",
                                      self.window.width - 5, self.window.height,
                                      arcade.color.BLACK, 72, self.window.width,
                                      "right", "bananaslip plus",
                                      anchor_x = "right", anchor_y = "top", multiline = True)
        self.data_text = arcade.Text(f"{self.results.fc_type}\nAccuracy: {self.results.accuracy * 100:.2f}%\nMax Streak: {self.results.max_streak}",
                                     self.window.width - 5, self.score_text.bottom,
                                     arcade.color.BLACK, 24, self.window.width,
                                     "right", "bananaslip plus",
                                     anchor_x = "right", anchor_y = "top", multiline = True)
        self.judgements_text = arcade.Text("", self.grade_sprite.right + 10, self.grade_sprite.bottom, arcade.color.BLACK, 24,
                                           self.window.width, anchor_x = "left", anchor_y = "bottom",
                                           font_name = "bananaslip plus", multiline = True)

        for j in self.results.judgements:
            self.judgements_text.value += f"{j.name}: {len([i for i in self.results.all_judgements if i[2] == j])}\n"

        self.heatmap = Heatmap(self.results.judgements, self.results.all_judgements)
        self.heatmap.scale = 2
        self.heatmap.bottom = 10
        self.heatmap.right = self.window.width - 10

        self.sprites = arcade.SpriteList()
        self.sprites.append(self.heatmap)

        # Save score
        ScoreDB(paths.scorespath).add_score(self.results.chart.hash, self.results)

        # Generate "gum wrapper" background
        self.logo_width, self.small_logos_forward, self.small_logos_backward = generate_gum_wrapper(self.size)
        self.success = True

    @shows_errors
    def on_show_view(self) -> None:
        self.window.theme_song.volume = 0
        VOLUME = 1
        self.song = arcade.play_sound(self._song, VOLUME, loop=False)

    @shows_errors
    @ignore_imgui
    def on_key_press(self, symbol: int, modifiers: int) -> None:
        keymap = get_keymap()
        match symbol:
            case keymap.back | keymap.start:
                self.song.volume = 0
                self.back.setup()
                self.window.show_view(self.back)
                arcade.play_sound(self.window.sounds["back"], volume = settings.get_volume("sound"))

        super().on_key_press(symbol, modifiers)

    @shows_errors
    def on_update(self, delta_time) -> None:
        super().on_update(delta_time)

        move_gum_wrapper(self.logo_width, self.small_logos_forward, self.small_logos_backward, delta_time)

    @shows_errors
    def on_draw(self) -> None:
        self.window.camera.use()
        self.clear()

        # Charm BG
        self.small_logos_forward.draw()
        self.small_logos_backward.draw()

        self.grade_sprite.draw()
        self.score_text.draw()
        self.data_text.draw()
        self.judgements_text.draw()
        self.sprites.draw()

        super().on_draw()
