from __future__ import annotations
from collections.abc import Iterator

from itertools import cycle

from arcade import SpriteList, Text, color as colors

from charm.lib.adobexml import sprite_from_adobe, AdobeSprite
from charm.lib.charm import GumWrapper
from charm.lib.digiview import DigiView
from charm.lib.keymap import keymap


class SpriteTestView(DigiView):
    def __init__(self, back: DigiView):
        super().__init__(fade_in=1, back=back)
        self.sprite: AdobeSprite
        self.anims: Iterator[str]
        self.anim_label: Text
        self.data_label: Text
        self.fps: int
        self.paused: bool
        self.gum_wrapper: GumWrapper
        self.sprite_list: SpriteList[AdobeSprite]

    def setup(self) -> None:
        super().presetup()
        SPRITE_NAME = "scott"
        SPRITE_ANIM = "idle"

        self.sprite = sprite_from_adobe(SPRITE_NAME, ("bottom", "left"))
        self.sprite_list = SpriteList()
        self.sprite_list.append(self.sprite)
        self.sprite.fps = 24
        self.sprite.bottom = 0
        self.sprite.left = 0
        self.sprite.set_animation(SPRITE_ANIM)
        self.anims = cycle(self.sprite.animations)
        self.anim_label = Text(SPRITE_ANIM, self.window.width // 2, self.window.height, font_size = 24, color = colors.BLACK, anchor_x="center", anchor_y="top")
        self.data_label = Text("", self.window.width, 0, font_size = 24, color = colors.BLACK, anchor_x="right", anchor_y="bottom", multiline=True, width=self.window.width, align="right")

        self.fps = self.sprite.fps
        self.paused = False

        self.gum_wrapper = GumWrapper()
        super().postsetup()

    def on_button_press(self, keymap: KeyMap) -> None:
        if keymap.back.pressed:
            self.go_back()
        elif keymap.start.pressed:
            self.cycle_anim()
        elif keymap.seek_backward.pressed:
            self.fps_down()
        elif keymap.seek_forward.pressed:
            self.fps_up()
        elif keymap.pause.pressed:
            self.toggle_pause()
        elif keymap.navleft.pressed:
            self.frame_back()
        elif keymap.navright.pressed:
            self.frame_forward()

    def on_button_release(self, keymap: KeyMap) -> None:
        pass

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        if self.paused:
            self.sprite.fps = 0
        else:
            self.sprite.fps = self.fps

    def cycle_anim(self) -> None:
        anim = next(self.anims)
        self.sprite.set_animation(anim)
        self.anim_label.text = anim

    def fps_up(self) -> None:
        self.sprite.fps += 1
        self.fps = self.sprite.fps

    def fps_down(self) -> None:
        self.sprite.fps -= 1
        self.fps = self.sprite.fps

    def frame_back(self) -> None:
        self.sprite.animation_frame -= 1

    def frame_forward(self) -> None:
        self.sprite.animation_frame += 1

    def on_update(self, delta_time: float) -> None:
        super().on_update(delta_time)
        self.sprite.update_animation(delta_time)
        st = self.sprite.animation_subtexture
        self.data_label.text = f"""
        Sprite FPS: {self.fps}
        Sprite F#: {self.sprite.animation_frame}
        X,Y,W,H: {st.x}, {st.y}, {st.width}, {st.height}
        FX,FY,FW,FH: {st.frame_x}, {st.frame_y}, {st.frame_width}, {st.frame_height}"""
        self.gum_wrapper.on_update(delta_time)

    def on_draw(self) -> None:
        super().predraw()
        self.gum_wrapper.draw()
        if self.sprite_list:
            self.sprite_list.draw()
            self.anim_label.draw()
            self.data_label.draw()
        super().postdraw()
