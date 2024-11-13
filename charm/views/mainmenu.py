import arcade
from arcade import color as colors, MOUSE_BUTTON_LEFT

from charm.lib.anim import ease_quartout, perc
from charm.lib.charm import GumWrapper
from charm.lib.digiview import DigiView, disable_when_focus_lost, shows_errors
from charm.lib.errors import TestError
from charm.lib.keymap import KeyMap
from charm.objects.mainmenu import MainMenu, MainMenuItem
# from charm.views.cycletest import CycleTestView
# from charm.views.emojitest import EmojiTestView
# from charm.views.fourkeysongmenu import FourKeySongMenuView
# from charm.views.herotest import HeroTestView
#from charm.views.taikosongtest import TaikoSongTestView
# from charm.views.newmenu import NewMenuView
from charm.views.gumwrapper import GumWrapperView
from charm.views.spritetest import SpriteTestView
from charm.views.visualizertest import VisualizerView
from charm.views.options import OptionsView
from charm.views.unifiedmenu import UnifiedSongMenuView
from charm.views.settings import SettingsView

class MainMenuView(DigiView):
    def __init__(self, back: DigiView):
        super().__init__(fade_in=1, back=back)
        self.menu = MainMenu([
            MainMenuItem("Play", "songs", UnifiedSongMenuView(back=self)),
            # MainMenuItem("Playlists", "playlists", None),
            MainMenuItem("Options", "options", OptionsView(back=self)),
            MainMenuItem("Settings", "options", SettingsView(back=self)),
            # MainMenuItem("4K Songs", "songs", FourKeySongMenuView(back=self)),
            # MainMenuItem("Emoji Test", "test", EmojiTestView(back=self)),
            # MainMenuItem("Menu Test", "test", NewMenuView(back=self)),
            # MainMenuItem("Cycler Test", "test", CycleTestView(back=self)),
            # MainMenuItem("Hero Test", "test", HeroTestView(back=self)),
            # MainMenuItem("Taiko Test", "test", TaikoSongTestView(back=self)),
            MainMenuItem("Sprite Test", "test", SpriteTestView(back=self)),
            MainMenuItem("Scott Test", "test", VisualizerView(back=self)),
            MainMenuItem("Gumwrapper", "test", GumWrapperView(back=self)),
        ])

    def setup(self) -> None:
        super().presetup()
        self.window.presence.set("In Menus")
        self.load_countdown = None
        super().postsetup()

    def on_hide_view(self) -> None:
        if self.menu is not None:
            self.menu.loading = False

    def on_show_view(self) -> None:
        super().on_show_view()
        if self.menu is not None:
            self.menu.loading = False

    @shows_errors
    def on_button_press(self, keymap: KeyMap) -> None:
        if keymap.navright.pressed:
            self.menu.selected_id += 1
        if keymap.navleft.pressed:
            self.menu.selected_id -= 1
        elif keymap.back.pressed:
            self.go_back()
        elif keymap.start.pressed:
            if self.menu.selected.goto is not None:
                self.menu.loading = True
                self.load_countdown = 3  # Pause for three frames before loading. Ensure the text draws.
            else:
                self.menu.selected.jiggle_start = self.local_time
        elif keymap.debug_e.pressed:
            raise TestError("You hit the E button! Don't do that.")
        elif keymap.debug_f24.pressed:
            raise TestError("F24, let's go!")

    @shows_errors
    def on_button_release(self, keymap: KeyMap) -> None:
        pass

    @shows_errors
    @disable_when_focus_lost(mouse=True)
    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> None:
        self.menu.selected_id += int(scroll_y)
        self.sfx.select.play()

    @shows_errors
    @disable_when_focus_lost(mouse=True)
    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int) -> None:
        if button == MOUSE_BUTTON_LEFT:
            clicked_item = self.menu.get_item_at(x, y)
            if clicked_item is not None:
                clicked_item.go()
            else:
                self.menu.selected.start_jiggle()

    @shows_errors
    def on_resize(self, width: int, height: int) -> None:
        self.menu.recreate()
        super().on_resize(width, height)

    @shows_errors
    def on_update(self, delta_time: float) -> None:
        super().on_update(delta_time)
        self.wrapper.update(delta_time)
        self.menu.on_update(delta_time)

    def countdown(self) -> None:
        if self.load_countdown is not None:
            self.load_countdown -= 1
        if self.load_countdown == 0:
            self.load_countdown = None
            self.menu.selected.go()

    @shows_errors
    def on_draw(self) -> None:
        super().predraw()
        # Charm BG
        self.wrapper.draw()
        left = ease_quartout(self.size[0], 0, perc(0.5, 1.5, self.local_time))
        arcade.draw_lrbt_rectangle_filled(left, self.size[0], self.size[1] // 4, (self.size[1] // 4) * 3, colors.WHITE[:3] + (127,))

        self.countdown()
        self.menu.draw()
        super().postdraw()
