from bisect import insort
from pyglet.math import Vec2
import arcade

from arcade import camera, BasicSprite, SpriteList, SpriteCircle

from charm.lib.keymap import keymap
from charm.lib.digiview import DigiView


class SpriteLayer[T: BasicSprite]:
    def __init__(self, *, z: float = 1.0) -> None:
        self.sprites = SpriteList[T]()
        self.camera = camera.Camera2D()
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


colors = [
    arcade.color.WHITE,
    arcade.color.RED,
    arcade.color.ORANGE,
    arcade.color.YELLOW,
    arcade.color.GREEN,
    arcade.color.CYAN,
    arcade.color.BLUE,
    arcade.color.INDIGO,
    arcade.color.VIOLET,
    arcade.color.MAGENTA
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
        arcade.set_background_color(arcade.color.BLACK)

        self.parallax = SpriteLayerList[SpriteCircle]()
        for i in range(1, DEPTH + 1):
            sprite_layer = SpriteLayer[SpriteCircle](z = i * 0.25)
            color = colors[i % len(colors)]
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
        if keymap.parallax_up.held:
            self.parallax.y += delta_time * PX_PER_S
        if keymap.parallax_down.held:
            self.parallax.y -= delta_time * PX_PER_S
        if keymap.parallax_left.held:
            self.parallax.x -= delta_time * PX_PER_S
        if keymap.parallax_right.held:
            self.parallax.x += delta_time * PX_PER_S
        if keymap.parallax_zoom_in.held:
            for layer in self.parallax.sprite_layers:
                layer.z *= 1 + delta_time
        if keymap.parallax_zoom_out.held:
            for layer in self.parallax.sprite_layers:
                layer.z /= 1 + delta_time
        return super().on_update(delta_time)

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        super().on_key_press(symbol, modifiers)
        if keymap.back.pressed:
            self.go_back()

    def on_draw(self) -> None:
        super().predraw()
        self.parallax.draw()
        super().postdraw()
