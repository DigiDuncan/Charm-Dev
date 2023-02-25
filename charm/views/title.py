import getpass
import importlib.resources as pkg_resources
import random

import arcade

import charm.data.audio
import charm.data.images
from charm.lib.anim import bounce, ease_linear, ease_quadinout
from charm.lib.charm import CharmColors, generate_gum_wrapper, move_gum_wrapper
from charm.lib.digiview import DigiView
from charm.lib.keymap import get_keymap
from charm.lib.utils import img_from_resource
from charm.views.mainmenu import MainMenuView

FADE_DELAY = 1
SWITCH_DELAY = 0.5 + FADE_DELAY


class TitleView(DigiView):
    def __init__(self):
        super().__init__(bg_color=CharmColors.FADED_GREEN)
        self.logo = None
        self.song = None
        self.volume = 0.1
        self.sounds: dict[str, arcade.Sound] = {}
        self.main_menu_view = MainMenuView(back=self)
        # Play music
        with pkg_resources.path(charm.data.audio, "song.mp3") as p:
            song = arcade.Sound(p)
            self.window.theme_song = arcade.play_sound(song, self.volume, looping=True)
        self.window.theme_song.seek(self.local_time + 3)

    def setup(self):
        self.hit_start = None
        self.local_time = 0

        arcade.set_background_color(CharmColors.FADED_GREEN)
        self.main_sprites = arcade.SpriteList()

        # Set up main logo
        logo_img = img_from_resource(charm.data.images, "logo.png")
        logo_texture = arcade.Texture(logo_img)
        self.logo = arcade.Sprite(logo_texture)
        self.logo.scale = 1 / 3
        self.logo.center_x = self.size[0] // 2
        self.logo.bottom = self.size[1] // 2

        self.main_sprites.append(self.logo)

        self.splashes = pkg_resources.read_text(charm.data, "splashes.txt").splitlines()
        self.splash_text = ""
        self.splash_index = 0
        self.egg_roll = random.randint(1, 1000)
        self.generate_splash()

        # Generate "gum wrapper" background
        self.logo_width, self.small_logos_forward, self.small_logos_backward = generate_gum_wrapper(self.size)

        # Song details
        self.song_label = arcade.pyglet.text.Label("Run Around The Character Code!\nCamellia feat. nanahira\n3LEEP!",
                          width=540,
                          font_name='bananaslip plus',
                          font_size=16,
                          x=5, y=5,
                          anchor_x='left', anchor_y='bottom',
                          multiline=True,
                          color=CharmColors.PURPLE)
        self.song_label.original_x = self.song_label.x
        self.song_label.x = -self.song_label.width

        # Press start prompt
        self.press_label = arcade.pyglet.text.Label("<press start>",
                          font_name='bananaslip plus',
                          font_size=32,
                          x=self.window.width // 2, y=self.window.height // 4,
                          anchor_x='center', anchor_y='center',
                          color=CharmColors.PURPLE)

        self.welcome_label = arcade.Text(f"welcome, {getpass.getuser()}!",
                          font_name='bananaslip plus',
                          font_size=14,
                          start_x=self.window.width // 2, start_y=6,
                          anchor_x='center', anchor_y='bottom',
                          color=arcade.color.BLACK)

    def generate_splash(self):
        if self.egg_roll == 666:
            # it's tricky
            self.splash_text = ""
            self.splash_label = arcade.Text("CLOWN KILLS YOU",
                          font_name='Impact',
                          font_size=48,
                          start_x=self.window.width // 2 + 100, start_y=self.window.height // 2,
                          anchor_x='center', anchor_y='top',
                          color=arcade.color.RED)
        else:
            self.splash_text = random.choice(self.splashes)
            self.splash_index = self.splashes.index(self.splash_text)
            self.splash_label = arcade.pyglet.text.Label("",
                            font_name='bananaslip plus',
                            font_size=24,
                            x=self.window.width // 2, y=self.window.height // 2,
                            anchor_x='left', anchor_y='top',
                            color=CharmColors.PURPLE)

    def on_key_press(self, symbol: int, modifiers: int):
        keymap = get_keymap()
        match symbol:
            case keymap.start:
                self.hit_start = self.local_time
                arcade.play_sound(self.window.sounds["valid"])
        if self.window.debug:
            match symbol:
                case arcade.key.S:
                    self.splash_index += 1
                    self.splash_index %= len(self.splashes)
                    self.splash_text = self.splashes[self.splash_index]
                case arcade.key.T:
                    self.egg_roll = 666 if self.egg_roll != 666 else 0
                    self.generate_splash()
                case arcade.key.KEY_0:
                    self.window.theme_song.seek(3)
                    self.setup()

        return super().on_key_press(symbol, modifiers)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.hit_start = self.local_time
            arcade.play_sound(self.window.sounds["valid"])

    def on_update(self, delta_time):
        self.local_time += delta_time

        move_gum_wrapper(self.logo_width, self.small_logos_forward, self.small_logos_backward, delta_time)

        # Logo bounce
        m = 0.325
        bpm = 220
        n = 0.3
        self.logo.scale = bounce(n, m, bpm, self.window.time)

        # Splash text typewriter effect
        if self.egg_roll == 666:
            self.splash_label.rotation = (random.random() * 10) - 5
        else:
            self.splash_label.rotation = 0
            self.splash_label.text = self.splash_text[:max(0, int((self.local_time - 3) * 20))]

        # Song name in and out
        if 3 <= self.local_time <= 5:  # constraining the time when we update the position should decrease lag,
                                       # even though it's technically unnecessary because the function is clamped
            self.song_label.x = ease_quadinout(-self.song_label.width, self.song_label.original_x, 3, 5, self.local_time)
        elif 8 <= self.local_time <= 10:
            self.song_label.x = ease_quadinout(self.song_label.original_x, -self.song_label.width, 8, 10, self.local_time)

        if self.hit_start is not None:
            # Fade music
            if self.local_time >= self.hit_start + FADE_DELAY:
                self.window.theme_song.volume = ease_linear(self.volume, self.volume / 2, self.hit_start + FADE_DELAY, self.hit_start + SWITCH_DELAY, self.local_time)
            # Go to main menu
            if self.local_time >= self.hit_start + SWITCH_DELAY:
                self.main_menu_view.setup()
                self.window.show_view(self.main_menu_view)

    def on_draw(self):
        self.clear()
        self.camera.use()

        # Charm BG
        self.small_logos_forward.draw()
        self.small_logos_backward.draw()

        arcade.draw_polygon_filled(
            [(self.welcome_label.x - self.welcome_label._label.content_width // 2, self.welcome_label._label.content_height + 10),
            (self.welcome_label.x - self.welcome_label._label.content_width // 2 + self.welcome_label._label.content_width, self.welcome_label._label.content_height + 10),
            (self.welcome_label.x - self.welcome_label._label.content_width // 2 + self.welcome_label._label.content_width + 20, 0), (self.welcome_label.x - self.welcome_label._label.content_width // 2 - 20, 0)],
            CharmColors.FADED_PURPLE
        )

        self.welcome_label.draw()

        # Logo and text
        self.main_sprites.draw()
        with self.window.ctx.pyglet_rendering():
            self.splash_label.draw()
            self.song_label.draw()
            if self.hit_start is None:
                if int(self.local_time) % 2:
                    self.press_label.draw()
            else:
                if int(self.local_time * 8) % 2:
                    self.press_label.draw()

        super().on_draw()
