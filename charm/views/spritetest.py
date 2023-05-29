from itertools import cycle
import arcade
from charm.lib.adobexml import sprite_from_adobe

from charm.lib.charm import CharmColors, generate_gum_wrapper, move_gum_wrapper
from charm.lib.digiview import DigiView
from charm.lib.keymap import get_keymap


class SpriteTestView(DigiView):
    def __init__(self, *args, **kwargs):
        super().__init__(fade_in=1, bg_color=CharmColors.FADED_GREEN, *args, **kwargs)

    def setup(self):
        super().setup()

        SPRITE_NAME = "scott"
        SPRITE_ANIM = "idle"

        self.sprite = sprite_from_adobe(SPRITE_NAME, ("bottom", "left"))
        self.sprite.fps = 24
        self.sprite.bottom = 0
        self.sprite.left = 0
        self.sprite.set_animation(SPRITE_ANIM)
        self.anims = cycle(self.sprite.animations)
        self.anim_label = arcade.Text(SPRITE_ANIM, self.window.width // 2, self.window.height, font_size = 24, color = arcade.color.BLACK, anchor_x="center", anchor_y="top")
        self.data_label = arcade.Text("", self.window.width, 0, font_size = 24, color = arcade.color.BLACK, anchor_x="right", anchor_y="bottom", multiline=True, width=self.window.width, align="right")

        self.fps = self.sprite.fps
        self.paused = False

        # Generate "gum wrapper" background
        self.logo_width, self.small_logos_forward, self.small_logos_backward = generate_gum_wrapper(self.size)

    def on_key_press(self, symbol: int, modifiers: int):
        keymap = get_keymap()
        match symbol:
            case keymap.back:
                self.back.setup()
                self.window.show_view(self.back)
                arcade.play_sound(self.window.sounds["back"])
            case keymap.start:
                a = next(self.anims)
                self.sprite.set_animation(a)
                self.anim_label.text = a
            case arcade.key.MINUS:
                self.sprite.fps -= 1
                self.fps = self.sprite.fps
            case arcade.key.EQUAL:
                self.sprite.fps += 1
                self.fps = self.sprite.fps
            case keymap.pause:
                self.paused = not self.paused
                if self.paused:
                    self.sprite.fps = 0
                else:
                    self.sprite.fps = self.fps
            case arcade.key.LEFT:
                self.sprite._current_animation_index -= 1
                self.sprite._current_animation_index %= len(self.sprite._current_animation)
            case arcade.key.RIGHT:
                self.sprite._current_animation_index += 1
                self.sprite._current_animation_index %= len(self.sprite._current_animation)

        return super().on_key_press(symbol, modifiers)

    def on_update(self, delta_time):
        super().on_update(delta_time)
        self.sprite.update_animation(delta_time)
        st = self.sprite._current_animation_sts[self.sprite._current_animation_index]
        self.data_label.text = f"""
        Sprite FPS: {self.fps}
        Sprite F#: {self.sprite._current_animation_index}
        X,Y,W,H: {st.x}, {st.y}, {st.width}, {st.height}
        FX,FY,FW,FH: {st.frame_x}, {st.frame_y}, {st.frame_width}, {st.frame_height}"""

        move_gum_wrapper(self.logo_width, self.small_logos_forward, self.small_logos_backward, delta_time)

    def on_draw(self):
        self.clear()
        self.camera.use()

        # Charm BG
        self.small_logos_forward.draw()
        self.small_logos_backward.draw()

        self.sprite.draw()
        self.anim_label.draw()
        self.data_label.draw()

        super().on_draw()
