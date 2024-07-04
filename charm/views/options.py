import logging

from charm.lib.charm import GumWrapper
from charm.lib.digiview import DigiView, shows_errors, disable_when_focus_lost
from charm.lib.settings import settings
from charm.lib.keymap import keymap

logger = logging.getLogger("charm")


class OptionsView(DigiView):
    def __init__(self, back: DigiView):
        super().__init__(fade_in=1, back=back)

    @shows_errors
    def setup(self) -> None:
        super().presetup()
        self.gum_wrapper = GumWrapper()
        super().postsetup()

    def on_show_view(self) -> None:
        self.window.theme_song.volume = 0

    @shows_errors
    @disable_when_focus_lost(keyboard=True)
    def on_key_press(self, symbol: int, modifiers: int) -> None:
        super().on_key_press(symbol, modifiers)
        if keymap.back.pressed:
            self.go_back()
        elif keymap.navup.pressed:
            self.volume_up(0.1)
        elif keymap.navdown.pressed:
            self.volume_down(0.1)

    def volume_up(self, factor: float):
        settings.volume.master = min(1.0, settings.volume.master + factor)
        print(settings.volume.master)
        self.sfx.select.play()

    def volume_down(self, factor: float):
        settings.volume.master = max(0.0, settings.volume.master - factor)
        print(settings.volume.master)
        self.sfx.select.play()

    @shows_errors
    def on_update(self, delta_time: float) -> None:
        super().on_update(delta_time)
        self.gum_wrapper.on_update(delta_time)

    @shows_errors
    def on_draw(self) -> None:
        super().predraw()
        # Charm BG
        self.gum_wrapper.draw()
        super().postdraw()
