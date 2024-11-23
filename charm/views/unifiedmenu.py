import logging

from charm.lib.charm import GumWrapper
from charm.lib.digiview import DigiView, shows_errors, disable_when_focus_lost
from charm.lib.keymap import KeyMap

# -- UI --
from charm.lib.mini_mint import Animator, Element
from charm.ui.menu_list import UnifiedChartsetMenuElement

# -- TEMP --
from charm.core.loading import load_chartsets, load_chart
from charm.core.loading2 import CHART_LOADER
from charm.views.game import GameView

logger = logging.getLogger("charm")


class UnifiedSongMenuView(DigiView):
    def __init__(self, back: DigiView):
        super().__init__(fade_in=1, back=back)
        if not CHART_LOADER.is_finished:
            CHART_LOADER.start_loading()
        self.animator: Animator = Animator()
        Element.Animator = self.animator
        self.element = UnifiedChartsetMenuElement(right_fraction=0.6)
        self.element.bounds = self.window.rect
        self.element.set_chartsets(CHART_LOADER.copy_chartsets())

    @shows_errors
    def setup(self) -> None:
        super().presetup()
        self.element.bounds = self.window.rect
        self.element.set_chartsets(CHART_LOADER.copy_chartsets())
        super().postsetup()

    def on_resize(self, width: int, height: int) -> None:
        self.element.bounds = self.window.rect
        super().on_resize(width, height)

    def on_show_view(self) -> None:
        super().on_show_view()
        self.window.theme_song.volume = 0
        for element in self.element.element_list.children:
            element.deselect()
            

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> bool | None:
        # TODO: Move this to the actual song element list, and also allow for using the mouse to
        # highlight/select a song or chart.
        return
        if self.element.bounds.point_in_bounds((x, y)):
            for child in self.element.element_list.children:
                if child.bounds.point_in_bounds((x, y)) and child.song is not None:
                    self.element.select_set(child.song)
                    self.element.highlighted_set_idx = self.element.chartsets.index(child.song)

    @shows_errors
    def on_button_press(self, keymap: KeyMap) -> None:
        if keymap.back.pressed:
            self.go_back()
        elif keymap.navdown.pressed:
            self.element.down_scroll()
        elif keymap.navup.pressed:
            self.element.up_scroll()
        elif keymap.start.pressed:
            if self.element.current_selected_chartset is not None:
                charset = self.element.current_selected_chartset
                chartdata = self.element.current_selected_chartset.charts[self.element.highlighted_chart_idx]
                charts = load_chart(chartdata)

                game_view = GameView()
                game_view.initialize_chart(charset, charts)

                game_view.setup()
                self.window.show_view(game_view)
            else:
                self.element.select_currently_highlighted()

    def on_button_release(self, keymap: KeyMap) -> None:
        pass

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> bool | None:
        if scroll_y > 0:
            self.element.up_scroll(int(abs(scroll_y)))
        elif scroll_y < 0:
            self.element.down_scroll(int(abs(scroll_y)))

    @shows_errors
    def on_update(self, delta_time: float) -> None:
        super().on_update(delta_time)
        self.wrapper.update(delta_time)
        self.animator.update(delta_time)

        if not CHART_LOADER.is_finished or not CHART_LOADER.is_up_to_date(self.element.chartsets):
            self.element.set_chartsets(CHART_LOADER.copy_chartsets())

    @shows_errors
    def on_fixed_update(self, delta_time: float) -> None:
        super().on_fixed_update(delta_time)
        self.animator.fixed_update(delta_time)

    @shows_errors
    def on_draw(self) -> None:
        super().predraw()
        # Charm BG
        self.wrapper.draw()
        self.element.draw()
        super().postdraw()
