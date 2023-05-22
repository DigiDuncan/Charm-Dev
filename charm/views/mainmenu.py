import arcade

from charm.lib.anim import ease_quartout
from charm.lib.charm import CharmColors, generate_gum_wrapper, move_gum_wrapper
from charm.lib.digiview import DigiView, shows_errors
from charm.lib.errors import TestError
from charm.lib.keymap import get_keymap
from charm.objects.menu import MainMenu, MainMenuItem
from charm.views.banner import BannerView
from charm.views.fnfsongmenu import FNFSongMenuView
from charm.views.fourkeysongmenu import FourKeySongMenuView
from charm.views.herotest import HeroTestView
from charm.views.newmenuview import NewMenuView
from charm.views.parallaxtest import ParallaxView
from charm.views.spritetest import SpriteTestView
from charm.views.subtitletest import SubtitleView
from charm.views.visualizer import VisualizerView


class MainMenuView(DigiView):
    def __init__(self, *args, **kwargs):
        super().__init__(fade_in=1, bg_color=CharmColors.FADED_GREEN, *args, **kwargs)

    def setup(self):
        super().setup()

        # Generate "gum wrapper" background
        self.logo_width, self.small_logos_forward, self.small_logos_backward = generate_gum_wrapper(self.size)

        self.menu = MainMenu(
            [
                MainMenuItem("Playlists", "playlists", None),
                MainMenuItem("FNF Songs", "songs", FNFSongMenuView(back=self)),
                MainMenuItem("4K Songs", "songs", FourKeySongMenuView(back=self)),
                MainMenuItem("Options", "options", None),
                MainMenuItem("Banner", "test", BannerView(back=self)),
                MainMenuItem("Menu Test", "test", NewMenuView(back=self)),
                MainMenuItem("Sprite Test", "test", SpriteTestView(back=self)),
                MainMenuItem("Lyric Test", "test", SubtitleView(back=self)),
                MainMenuItem("Parallax Test", "test", ParallaxView(back=self)),
                MainMenuItem("Hero Test", "test", HeroTestView(back=self)),
                MainMenuItem("Scott Test", "test", VisualizerView(back=self))
            ]
        )

        self.window.current_rp_state = "In Menus"
        self.window.update_rp("In Menus")

        self.load_countdown = None

    def load(self):
        self.menu.selected.goto.setup()
        self.window.show_view(self.menu.selected.goto)
        arcade.play_sound(self.window.sounds["valid"])

    @shows_errors
    def on_key_press(self, symbol: int, modifiers: int):
        keymap = get_keymap()
        match symbol:
            case arcade.key.RIGHT:
                self.menu.selected_id += 1
            case arcade.key.LEFT:
                self.menu.selected_id -= 1
            case keymap.back:
                self.back.setup()
                self.window.show_view(self.back)
                arcade.play_sound(self.window.sounds["back"])
            case keymap.start:
                if self.menu.selected.goto is not None:
                    self.menu.loading = True
                    self.load_countdown = 3  # Pause for three frames before loading. Ensure the text draws.
                else:
                    self.menu.selected.jiggle_start = self.local_time
            case arcade.key.E:
                raise TestError("You hit the E button! Don't do that.")
            case arcade.key.F24:
                raise TestError("F24, let's go!")

        return super().on_key_press(symbol, modifiers)

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        self.menu.selected_id += int(scroll_y)
        arcade.play_sound(self.window.sounds["select"])

    @shows_errors
    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        if button == arcade.MOUSE_BUTTON_LEFT:
            for item in self.menu.items:
                if item.collides_with_point((x, y)):
                    if item.goto is not None:
                        item.goto.setup()
                        self.window.show_view(item.goto)
                        arcade.play_sound(self.window.sounds["valid"])
                        break
            else:
                self.menu.selected.jiggle_start = self.local_time

    @shows_errors
    def on_update(self, delta_time):
        super().on_update(delta_time)

        move_gum_wrapper(self.logo_width, self.small_logos_forward, self.small_logos_backward, delta_time)
        self.menu.update(self.local_time)

        if self.load_countdown is not None:
            self.load_countdown -= 1
        if self.load_countdown == 0:
            self.load()

    @shows_errors
    def on_draw(self):
        self.clear()
        self.camera.use()

        # Charm BG
        self.small_logos_forward.draw()
        self.small_logos_backward.draw()

        left = ease_quartout(self.size[0], 0, 0.5, 1.5, self.local_time)
        arcade.draw_lrtb_rectangle_filled(left, self.size[0], (self.size[1] // 4) * 3, self.size[1] // 4, arcade.color.WHITE[:3] + (127,))

        self.menu.draw()

        super().on_draw()
