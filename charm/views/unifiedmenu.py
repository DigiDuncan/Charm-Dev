import logging

from charm.lib.charm import GumWrapper
from charm.lib.digiview import DigiView, shows_errors, disable_when_focus_lost
from charm.lib.keymap import keymap

# -- UI --
from charm.lib.mini_mint import Animator, Element
from charm.ui.menu_list import SongMenuListElement
from charm.ui.menu_list.song_stub import Song, Chart, Metadata

# -- TEMP --
from charm.lib.songloader import load_songs_and_chart_stub_fnf

logger = logging.getLogger("charm")


class UnifiedSongMenuView(DigiView):
    def __init__(self, back: DigiView):
        super().__init__(fade_in=1, back=back)
        self.animator: Animator = Animator()
        Element.Animator = self.animator
        self.element = SongMenuListElement(right_fraction=0.6)
        self.element.bounds = self.window.rect
        self.element.set_songs(load_songs_and_chart_stub_fnf())

    @shows_errors
    def setup(self) -> None:
        super().presetup()
        self.gum_wrapper = GumWrapper()
        super().postsetup()

    def on_resize(self, width: int, height: int) -> None:
        self.element.bounds = self.window.rect
        super().on_resize(width, height)

    def on_show_view(self) -> None:
        self.window.theme_song.volume = 0

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> bool | None:
        # TODO: Move this to the actual song element list, and also allow for using the mouse to
        # highlight/select a song or chart.
        if self.element.bounds.point_in_bounds((x, y)):
            for child in self.element.element_list.children:
                if child.bounds.point_in_bounds((x, y)) and child.song is not None:
                    self.element.select_song(child.song)
                    self.element.highlighted_song_idx = self.element.songs.index(child.song)

    @shows_errors
    @disable_when_focus_lost(keyboard=True)
    def on_key_press(self, symbol: int, modifiers: int) -> None:
        super().on_key_press(symbol, modifiers)
        if keymap.back.pressed:
            self.go_back()
        elif keymap.navdown.pressed:
            self.element.down_scroll()
        elif keymap.navup.pressed:
            self.element.up_scroll()
        elif keymap.start.pressed:
            # ! Warning this is Windows and FNF specific
            if self.element.current_selected_song is not None:
                song = self.element.current_selected_song
                chart = self.element.current_selected_song.charts[self.element.highlighted_chart_idx]
            else:
                self.element.select_currently_highlighted()

    @shows_errors
    def on_update(self, delta_time: float) -> None:
        super().on_update(delta_time)
        self.gum_wrapper.on_update(delta_time)
        self.animator.update(delta_time)

    @shows_errors
    def on_fixed_update(self, delta_time: float) -> None:
        super().on_fixed_update(delta_time)
        self.animator.fixed_update(delta_time)

    @shows_errors
    def on_draw(self) -> None:
        super().predraw()
        # Charm BG
        self.gum_wrapper.draw()
        self.element.draw()
        super().postdraw()
