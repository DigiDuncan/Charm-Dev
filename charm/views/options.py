import logging

from arcade import Text
import arcade

from charm.lib.charm import GumWrapper
from charm.lib.digiview import DigiView, shows_errors, disable_when_focus_lost
from charm.lib.settings import settings
from charm.lib.keymap import KeyMap

logger = logging.getLogger("charm")


class OptionsView(DigiView):
    def __init__(self, back: DigiView):
        super().__init__(fade_in=1, back=back)

    @shows_errors
    def setup(self) -> None:
        super().presetup()
        self.haha = Text(f"VOLUME\n{round(settings.volume.master * 100)}%", (self.size[0] // 2), (self.size[1] // 2), font_size=128,
                    anchor_x="center", anchor_y="center", color=arcade.color.BLACK,
                    font_name="bananaslip plus", multiline = True, width = 1920,
                    align = "center")
        super().postsetup()

    def on_show_view(self) -> None:
        self.window.theme_song.volume = 0

    @shows_errors
    def on_button_press(self, keymap: KeyMap) -> None:
        if keymap.back.pressed:
            self.go_back()
        elif keymap.navup.pressed:
            self.volume_up(0.1)
        elif keymap.navdown.pressed:
            self.volume_down(0.1)

    @shows_errors
    def on_button_release(self, keymap: KeyMap) -> None:
        pass

    def volume_up(self, factor: float) -> None:
        settings.volume.master = min(1.0, settings.volume.master + factor)
        self.haha.text = f"VOLUME\n{round(settings.volume.master * 100)}%"
        self.sfx.select.play()

    def volume_down(self, factor: float) -> None:
        settings.volume.master = max(0.0, settings.volume.master - factor)
        self.haha.text = f"VOLUME\n{round(settings.volume.master * 100)}%"
        self.sfx.select.play()

    @shows_errors
    def on_update(self, delta_time: float) -> None:
        super().on_update(delta_time)
        self.wrapper.update(delta_time)

    @shows_errors
    def on_draw(self) -> None:
        super().predraw()
        # Charm BG
        self.wrapper.draw()
        self.haha.draw()
        super().postdraw()
