import arcade

class TransparencyWindow(arcade.Window):
    def __init__(self):
        super().__init__(1280, 720, "Transparency Test")

        self.show_bar = False

        SOLID_COLOR = (255, 0, 0)
        TRANSPARENT_COLOR = (255, 0, 0, 128)

        # No transparency
        self.texture = arcade.Texture.create_empty("the_texture_1", (100, 100))
        self.sprite = arcade.Sprite(self.texture)
        self.sprite.position = (100, 360)
        self.sprite_list = arcade.SpriteList()
        self.sprite_list.append(self.sprite)

        with self.sprite_list.atlas.render_into(self.texture) as fbo:
            fbo.clear()
            arcade.draw_arc_filled(50, 50, 40, 40, SOLID_COLOR, 0, 360)
            arcade.draw_arc_outline(50, 50, 40, 40, SOLID_COLOR, 0, 360, 3)

        # Transparency
        self.texture2 = arcade.Texture.create_empty("the_texture_2", (100, 100))
        self.sprite2 = arcade.Sprite(self.texture2)
        self.sprite2.position = (1180, 360)
        self.sprite_list2 = arcade.SpriteList()
        self.sprite_list2.append(self.sprite2)

        with self.sprite_list2.atlas.render_into(self.texture2) as fbo:
            fbo.clear()
            arcade.draw_arc_filled(50, 50, 40, 40, TRANSPARENT_COLOR, 0, 360)
            arcade.draw_arc_outline(50, 50, 40, 40, SOLID_COLOR, 0, 360, 3)

        self.sprite_list2.atlas.save("atlas.png")

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.B:
            self.show_bar = not self.show_bar

    def on_draw(self):
        self.clear(arcade.color.GRAY)
        if self.show_bar:
            arcade.draw_lrtb_rectangle_filled(0, 1280, 460, 260, (0, 0, 0, 128))
        self.sprite_list.draw()
        self.sprite_list2.draw()


def main():
    TransparencyWindow().run()


if __name__ == "__main__":
    main()
