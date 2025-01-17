from bisect import insort

import arcade
from arcade import BasicSprite, SpriteList, SpriteCircle, Camera2D, Vec2, color as colors

from charm.core.keymap import keymap
from charm.core.digiview import DigiView, shows_errors


class SpriteLayer[T: BasicSprite]:
    def __init__(self, *, z: float = 1.0) -> None:
        self.sprites = SpriteList[T]()
        self.camera = Camera2D()
        self.z = z

    @property
    def z(self) -> float:
        return self.camera.zoom ** -0.5

    @z.setter
    def z(self, value: float) -> None:
        self.camera.zoom = value ** -2

    @property
    def position(self) -> Vec2:
        return self.camera.position

    @position.setter
    def position(self, value: Vec2) -> None:
        self.camera.position = value

    @property
    def x(self) -> float:
        return self.position.x

    @x.setter
    def x(self, new_x: float) -> None:
        self.position = Vec2(new_x, self.position.y)

    @property
    def y(self) -> float:
        return self.position.y

    @y.setter
    def y(self, new_y: float) -> None:
        self.position = Vec2(self.position.x, new_y)

    def append(self, sprite: T) -> None:
        self.sprites.append(sprite)

    def draw(self) -> None:
        with self.camera.activate():
            self.sprites.draw()


class SpriteLayerList[T: BasicSprite]:
    def __init__(self) -> None:
        self.sprite_layers: list[SpriteLayer[T]] = []
        self._position = Vec2(0, 0)

    def append(self, sprite_layer: SpriteLayer[T]) -> None:
        insort(self.sprite_layers, sprite_layer, key=lambda x: -x.z)

    @property
    def position(self) -> Vec2:
        return self._position

    @position.setter
    def position(self, value: Vec2) -> None:
        self._position = value
        for layer in self.sprite_layers:
            layer.position = self._position

    @property
    def x(self) -> float:
        return self.position.x

    @x.setter
    def x(self, new_x: float) -> None:
        self.position = Vec2(new_x, self.position.y)

    @property
    def y(self) -> float:
        return self.position.y

    @y.setter
    def y(self, new_y: float) -> None:
        self.position = Vec2(self.position.x, new_y)

    def draw(self) -> None:
        for layer in self.sprite_layers:
            layer.draw()


charm_colors = [
    colors.WHITE,
    colors.RED,
    colors.ORANGE,
    colors.YELLOW,
    colors.GREEN,
    colors.CYAN,
    colors.BLUE,
    colors.INDIGO,
    colors.VIOLET,
    colors.MAGENTA
]

DEPTH = 20
WIDTH = 60
HEIGHT = 30
STEP = 100


class ParallaxTestView(DigiView):
    def __init__(self, back: DigiView):
        super().__init__(fade_in=1, back=back)
        self.parallax: SpriteLayerList[SpriteCircle]

    def setup(self) -> None:
        super().presetup()
        arcade.set_background_color(colors.BLACK)

        self.parallax = SpriteLayerList[SpriteCircle]()
        for i in range(1, DEPTH + 1):
            sprite_layer = SpriteLayer[SpriteCircle](z = i * 0.25)
            color = charm_colors[i % len(charm_colors)]
            for x in range(-(WIDTH * STEP) // 2, ((WIDTH * STEP) // 2) + 1, STEP):
                for y in range(-(HEIGHT * STEP) // 2, ((HEIGHT * STEP) // 2) + 1, STEP):
                    sprite = SpriteCircle(25, color, soft=True)
                    sprite.center_x = x
                    sprite.center_y = y
                    sprite_layer.append(sprite)
            self.parallax.append(sprite_layer)
        super().postsetup()

    def on_show_view(self) -> None:
        super().on_show_view()
        self.window.theme_song.volume = 0

    def on_update(self, delta_time: float) -> None:
        PX_PER_S = 100
        if keymap.parallax.up.held:
            self.parallax.y += delta_time * PX_PER_S
        if keymap.parallax.down.held:
            self.parallax.y -= delta_time * PX_PER_S
        if keymap.parallax.left.held:
            self.parallax.x -= delta_time * PX_PER_S
        if keymap.parallax.right.held:
            self.parallax.x += delta_time * PX_PER_S
        if keymap.parallax.zoom_in.held:
            for layer in self.parallax.sprite_layers:
                layer.z *= 1 + delta_time
        if keymap.parallax.zoom_out.held:
            for layer in self.parallax.sprite_layers:
                layer.z /= 1 + delta_time
        return super().on_update(delta_time)

    @shows_errors
    def on_button_press(self, keymap: KeyMap) -> None:
        if keymap.back.pressed:
            self.go_back()

    @shows_errors
    def on_button_release(self, keymap: KeyMap) -> None:
        pass

    def on_draw(self) -> None:
        super().predraw()
        self.parallax.draw()
        super().postdraw()
