from pathlib import Path
import PIL.Image
from arcade import Texture, TextureAnimationSprite, TextureAnimation, TextureKeyframe
from arcade.resources import resolve

class GIF(TextureAnimationSprite):
    def __init__(self, spritesheet: Path, rows: int, cols: int, frames: int, fps: float,
                 center_x: float = 0, center_y: float = 0):
        file_name = resolve(spritesheet)
        source_image = PIL.Image.open(file_name).convert("RGBA")

        texture_list: list[Texture] = []

        sprite_width = source_image.width // cols
        sprite_height = source_image.height // rows

        #     C0     C1     C2     C3     C4
        # R0 (0, 0) (1, 0) (2, 0) (3, 0) (4, 0)
        # R1 (0, 1) (1, 1) (2, 1) (3, 1) (4, 1)

        for sprite_no in range(frames):
            row = sprite_no // cols
            column = sprite_no % cols
            start_x = sprite_width * column
            start_y = sprite_height * row
            image = source_image.crop(
                (start_x, start_y, start_x + sprite_width, start_y + sprite_height)
            )
            texture = Texture(image)
            texture.file_path = file_name
            texture_list.append(texture)

        anim = TextureAnimation([TextureKeyframe(t, int((1 / fps) * 1000)) for t in texture_list])

        super().__init__(center_x = center_x, center_y = center_y, animation = anim)
