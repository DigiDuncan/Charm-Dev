import logging

import arcade
from pyglet.graphics import Batch

from charm.lib.charm import CharmColors, generate_gum_wrapper, move_gum_wrapper
from charm.lib.digiview import DigiView
from charm.lib.gamemodes.hero import HeroEngine, HeroHighway, HeroSong, SectionEvent
from charm.lib.keymap import get_keymap
from charm.lib.oggsound import OGGSound
from charm.lib.paths import songspath
from charm.lib.settings import settings
from charm.objects.lyric_animator import LyricAnimator

logger = logging.getLogger("charm")


class HeroTestView(DigiView):
    def __init__(self, *args, **kwargs):
        super().__init__(fade_in=1, bg_color=CharmColors.FADED_GREEN, *args, **kwargs)
        self.song = None
        self.highway = None
        self.volume = 0.25

    def setup(self):
        super().setup()

        # name = "mcmental"
        name = "run_around_the_character_code"

        self._song = OGGSound(songspath / "ch" / name / "song.ogg")
        self.hero_song = HeroSong.parse(songspath / "ch" / name)
        self.chart = self.hero_song.get_chart("Expert", "Single")
        self.engine = HeroEngine(self.chart)
        self.highway = HeroHighway(self.chart, (0, 0), auto = False)
        self.highway.x += self.window.width // 2 - self.highway.w // 2

        self.text_batch = Batch()

        metadata_string = f"{self.hero_song.metadata.title}\n{self.hero_song.metadata.artist}\n{self.hero_song.metadata.album}"
        self.metadata_text = arcade.Text(metadata_string, 5, 5, arcade.color.BLACK, 16, align = "left", anchor_x = "left", anchor_y = "bottom", multiline = True, font_name = "bananaslip plus", width=self.window.width, batch = self.text_batch)
        self.section_text = arcade.Text("", self.window.width - 5, 5, arcade.color.BLACK, 16, anchor_x = "right", font_name = "bananaslip plus", width=self.window.width, batch = self.text_batch)
        self.time_text = arcade.Text("0:00", self.window.width - 5, 35, arcade.color.BLACK, 16, anchor_x = "right", font_name = "bananaslip plus", width=self.window.width, batch = self.text_batch)
        self.score_text = arcade.Text("0", self.window.width - 5, 65, arcade.color.BLACK, 24, anchor_x = "right", font_name = "bananaslip plus", width=self.window.width, batch = self.text_batch)
        self.multiplier_text = arcade.Text("x1", self.window.width - 5, 95, arcade.color.BLACK, 16, anchor_x = "right", font_name = "bananaslip plus", width=self.window.width, batch = self.text_batch)

        self.lyric_animator = None
        if self.hero_song.lyrics:
            self.lyric_animator = LyricAnimator(self.window.width // 2, self.window.height - 100, self.hero_song.lyrics)
            self.lyric_animator.prerender()

        # Generate "gum wrapper" background
        self.logo_width, self.small_logos_forward, self.small_logos_backward = generate_gum_wrapper(self.size)

    def on_show_view(self):
        self.window.theme_song.volume = 0
        self.song = arcade.play_sound(self._song, self.volume, loop=False)

    def on_key_press(self, symbol: int, modifiers: int):
        keymap = get_keymap()
        keymap.set_state(symbol, True)
        self.engine.process_keystate()
        match symbol:
            case keymap.back:
                self.song.delete()
                self.back.setup()
                self.window.show_view(self.back)
                arcade.play_sound(self.window.sounds["back"], volume = settings.get_volume("sound"))
            case keymap.pause:
                self.song.pause() if self.song.playing else self.song.play()
        if self.window.debug:
            match symbol:
                case arcade.key.KEY_0:
                    self.song.seek(0)
                case arcade.key.MINUS:
                    self.song.seek(self.song.time - 5)
                case arcade.key.EQUAL:
                    self.song.seek(self.song.time + 5)
                case arcade.key.F:
                    self.highway.show_flags = not self.highway.show_flags

        return super().on_key_press(symbol, modifiers)

    def on_key_release(self, symbol: int, modifiers: int):
        keymap = get_keymap()
        keymap.set_state(symbol, False)
        self.engine.process_keystate()

    def on_update(self, delta_time):
        super().on_update(delta_time)

        self.highway.update(self.song.time)

        self.engine.update(self.song.time)
        self.engine.calculate_score()

        # Section name
        # This should in theory be kinda fast because it's using Indexes?
        current_section: SectionEvent = self.hero_song.indexes_by_time["section"].lteq(self.song.time)
        if current_section and self.section_text.text != current_section.name:
            logger.debug(f"Section name is now {current_section.name} ({self.song.time})")
            self.section_text.text = current_section.name

        time_string = f"{self.song.time // 60:.0f}:{int(self.song.time % 60):02}"
        if self.time_text.text != time_string:
            self.time_text.text = time_string

        if self.score_text._label.text != f"{self.engine.score}":
            self.score_text._label.text = f"{self.engine.score}"

        if self.multiplier_text._label.text != f"x{self.engine.multiplier} [{self.engine.combo}]":
            self.multiplier_text._label.text = f"x{self.engine.multiplier} [{self.engine.combo}]"

        if self.lyric_animator:
            self.lyric_animator.update(self.song.time)

        move_gum_wrapper(self.logo_width, self.small_logos_forward, self.small_logos_backward, delta_time)

    def on_draw(self):
        self.window.camera.use()
        self.clear()

        # Charm BG
        self.small_logos_forward.draw()
        self.small_logos_backward.draw()

        self.highway.draw()
        self.text_batch.draw()

        if self.lyric_animator:
            self.lyric_animator.draw()

        super().on_draw()
