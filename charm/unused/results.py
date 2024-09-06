from importlib.resources import files, as_file
import logging

import arcade
from arcade import Sprite, SpriteList, Text, Sound, color as colors
from pyglet.media import Player

from charm.lib.charm import GumWrapper
from charm.lib.digiview import DigiView, disable_when_focus_lost, shows_errors
from charm.lib.generic.results import Results, Heatmap
from charm.lib import paths

import charm.data.audio
import charm.data.images.skins as skins
from charm.lib.keymap import keymap
from charm.lib.scores import ScoreDB

logger = logging.getLogger("charm")


class ResultsView(DigiView):
    def __init__(self, back: DigiView, results: Results):
        super().__init__(fade_in=1, back=back)
        self.song: Player
        self.results = results

        self.song_sound: Sound = None
        self.grade_sprite: Sprite = None
        self.score_text: Text = None
        self.data_text: Text = None
        self.judgements_text: Text = None
        self.heatmap: Heatmap = None
        self.gum_wrapper: GumWrapper = None
        self.sprite_list: SpriteList = None
        self.success: bool = False

    @shows_errors
    def setup(self) -> None:
        super().presetup()
        with as_file(files(charm.data.audio) / "music-results.mp3") as p:
            self.song_sound = Sound(p)

        with as_file(files(skins) / "base" / f"grade-{self.results.grade}.png") as p:
            self.grade_sprite = Sprite(p)
        self.grade_sprite.bottom = 25
        self.grade_sprite.left = 25

        self.score_text = Text(f"{self.results.score}",
                                      self.window.width - 5, self.window.height,
                                      colors.BLACK, 72, self.window.width,
                                      "right", "bananaslip plus",
                                      anchor_x = "right", anchor_y = "top", multiline = True)
        self.data_text = Text(f"{self.results.fc_type}\nAccuracy: {self.results.accuracy * 100:.2f}%\nMax Streak: {self.results.max_streak}",
                                     self.window.width - 5, self.score_text.bottom,
                                     colors.BLACK, 24, self.window.width,
                                     "right", "bananaslip plus",
                                     anchor_x = "right", anchor_y = "top", multiline = True)
        self.judgements_text = Text("", self.grade_sprite.right + 10, self.grade_sprite.bottom, colors.BLACK, 24,
                                           self.window.width, anchor_x = "left", anchor_y = "bottom",
                                           font_name = "bananaslip plus", multiline = True)

        for j in self.results.judgements:
            self.judgements_text.value += f"{j.name}: {len([i for i in self.results.all_judgements if i[2] == j])}\n"

        self.heatmap = Heatmap(self.results.judgements, self.results.all_judgements)
        self.heatmap.scale = 2
        self.heatmap.bottom = 10
        self.heatmap.right = self.window.width - 10

        # Save score
        ScoreDB(paths.scorespath).add_score(self.results.chart.hash, self.results)

        self.sprite_list = SpriteList()
        self.sprite_list.extend((self.grade_sprite, self.heatmap))

        self.gum_wrapper = GumWrapper()
        self.success = True
        super().postsetup()

    @shows_errors
    def on_show_view(self) -> None:
        self.window.theme_song.volume = 0
        song = arcade.play_sound(self.song_sound, 0.25, loop=False)
        if song is not None:
            self.song = song

    @shows_errors
    @disable_when_focus_lost(keyboard=True)
    def on_key_press(self, symbol: int, modifiers: int) -> None:
        super().on_key_press(symbol, modifiers)
        if keymap.back.pressed or keymap.start.pressed:
            self.go_back()

    def go_back(self) -> None:
        self.song.volume = 0
        super().go_back()

    @shows_errors
    def on_update(self, delta_time: float) -> None:
        super().on_update(delta_time)
        self.gum_wrapper.on_update(delta_time)

    @shows_errors
    def on_draw(self) -> None:
        super().predraw()
        if self.success:
            self.gum_wrapper.draw()
            self.score_text.draw()
            self.data_text.draw()
            self.judgements_text.draw()
            self.sprite_list.draw()
        super().postdraw()
