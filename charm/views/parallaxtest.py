import arcade
from charm.lib.keymap import get_keymap
from pyglet.math import Vec2

from charm.lib.digiview import DigiView


class SpriteLayer:
    def __init__(self, sprite_list: arcade.SpriteList, z: float) -> None:
        self.sprite_list = sprite_list
        self._z = z
        self._camera = arcade.Camera()
        self._camera.scale = self._z ** 2

    @property
    def z(self) -> float:
        return self._z

    @z.setter
    def z(self, value: float):
        self._z = value
        self._camera.scale = self._z ** 2


class SpriteLayerList:
    def __init__(self, sprite_layers: list[SpriteLayer] = []) -> None:
        self.sprite_layers = sprite_layers
        self._position = Vec2(0, 0)

    @property
    def position(self) -> Vec2:
        return self._position

    @position.setter
    def position(self, value: Vec2):
        self._position = value
        for sl in self.sprite_layers:
            sl._camera.move(self._position)

    @property
    def x(self) -> float:
        return self._position.x

    @x.setter
    def x(self, value: float):
        self._position = Vec2(value, self._position.y)
        for sl in self.sprite_layers:
            sl._camera.move(self._position)

    @property
    def y(self) -> float:
        return self._position.y

    @y.setter
    def y(self, value: float):
        self._position = Vec2(self._position.x, value)
        for sl in self.sprite_layers:
            sl._camera.move(self._position)

    def sort(self):
        self.sprite_layers.sort(key=lambda x: x.z, reverse=True)

    def draw(self):
        for sl in self.sprite_layers:
            sl._camera.use()
            sl.sprite_list.draw()


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


class ParallaxView(DigiView):
    def __init__(self, *args, **kwargs):
        super().__init__(fade_in=1, bg_color=arcade.color.BLACK, *args, **kwargs)

    def setup(self):
        super().setup()
        self.parallax = SpriteLayerList()
        for i in range(1, DEPTH + 1):
            sprite_list = arcade.SpriteList()
            for j in range(-WIDTH // 2, (WIDTH // 2) + 1):
                for k in range(-HEIGHT // 2, (HEIGHT // 2) + 1):
                    sprite = arcade.SpriteCircle(25, colors[i % len(colors)], True)
                    sprite.center_x = j * 100
                    sprite.center_y = k * 100
                    sprite_list.append(sprite)
            self.parallax.sprite_layers.append(SpriteLayer(sprite_list, z = i * 0.25))
        self.parallax.sort()

    def on_show(self):
        super().on_show()
        self.window.theme_song.volume = 0

    def on_update(self, delta_time: float):
        PX_PER_S = 100
        if self.window.keyboard[arcade.key.W]:
            self.parallax.y += delta_time * PX_PER_S
        if self.window.keyboard[arcade.key.S]:
            self.parallax.y -= delta_time * PX_PER_S
        if self.window.keyboard[arcade.key.A]:
            self.parallax.x -= delta_time * PX_PER_S
        if self.window.keyboard[arcade.key.D]:
            self.parallax.x += delta_time * PX_PER_S
        if self.window.keyboard[arcade.key.R]:
            for sl in self.parallax.sprite_layers:
                sl.z *= 1 + delta_time
        if self.window.keyboard[arcade.key.F]:
            for sl in self.parallax.sprite_layers:
                sl.z /= 1 + delta_time

        return super().on_update(delta_time)

    def on_key_press(self, symbol: int, modifiers: int):
        keymap = get_keymap()
        match symbol:
            case keymap.back:
                self.back.setup()
                self.window.show_view(self.back)
                arcade.play_sound(self.window.sounds["back"])

        return super().on_key_press(symbol, modifiers)

    def on_draw(self):
        self.clear()
        self.camera.use()

        self.parallax.draw()

        super().on_draw()
