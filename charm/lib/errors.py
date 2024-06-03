from types import ModuleType
from typing import cast
import arcade
import arcade.color
import PIL, PIL.Image, PIL.ImageDraw  # noqa: E401
from arcade import Sprite, camera

import charm.data.images.errors
from charm.lib.utils import img_from_resource


class CharmException(Exception):
    def __init__(self, title: str, message: str, icon: str = "error"):
        self.title = title
        self.message = message
        self.icon_name = icon
        super().__init__(message)
        try:
            window = arcade.get_window()
        except RuntimeError:
            # If we aren't in an arcade Window (e.g., unit testing) we don't need the sprite stuff.
            return
        self.icon = img_from_resource(cast(ModuleType, charm.data.images.errors), f"{self.icon_name}.png")
        self.icon.resize((32, 32), PIL.Image.LANCZOS)
        self.sprite = self.get_sprite()
        self.sprite.position = (window.width / 2, window.height / 2)

    def get_sprite(self) -> Sprite:
        window = arcade.get_window()
        _tex = arcade.Texture.create_empty(f"_error-{self.title}-{self.message}", (500, 200))
        default_atlas = window.ctx.default_atlas
        default_atlas.add(_tex)

        _icon_tex = arcade.Texture(self.icon)
        default_atlas.add(_icon_tex)
        sprite = Sprite(_tex)

        with default_atlas.render_into(_tex) as fbo:
            l, b, w, h = fbo.viewport
            temp_cam = camera.Camera2D(
                viewport=(l, b, w, h),
                projection=(0, w, h, 0),
                position=(0.0, 0.0),
                render_target=fbo
            )
            with temp_cam.activate():
                fbo.clear()

                arcade.draw_lrbt_rectangle_filled(0, 500, 0, 200, arcade.color.BLANCHED_ALMOND)
                arcade.draw_lrbt_rectangle_filled(0, 500, 150, 200, arcade.color.BRANDEIS_BLUE)
                arcade.draw_text(self.title, 50, 165, font_size=24, bold=True, font_name="bananaslip plus")
                arcade.draw_text(self.message, 5, 146, font_size=16, anchor_y="top", multiline=True, width=492, color=arcade.color.BLACK, font_name="bananaslip plus")
                arcade.draw_texture_rectangle(25, 175, 32, 32, _icon_tex)

        return sprite


class GenericError(CharmException):
    def __init__(self, error: Exception):
        super().__init__(error.__class__.__name__, str(error))


class TestError(CharmException):
    def __init__(self, message: str):
        super().__init__("Test", message)


class NoChartsError(CharmException):
    def __init__(self, song_name: str):
        super().__init__("No charts found!", f"No charts found for song '{song_name}'")


class NoMetadataError(CharmException):
    def __init__(self, song_name: str):
        super().__init__("No metadata found!", f"No metadata found for song '{song_name}'")


class ChartParseError(CharmException):
    def __init__(self, line_num: int, message: str):
        super().__init__("Chart parsing error!", f"[Line {line_num}] {message}")


class MetadataParseError(CharmException):
    def __init__(self, message: str):
        super().__init__("Metadata parsing error!", message)


class ChartPostReadParseError(CharmException):
    def __init__(self, message: str):
        super().__init__("Chart post-read parse error!", message)


class UnknownLanesError(CharmException):
    def __init__(self, message: str):
        super().__init__("Unknown lanes found", message, "warning")


class TooManyKeyBindError(CharmException):
    def __init__(self, action: str):
        super().__init__(
            title="Too many key binds set!",
            message=f"Action '{action}' has too many key binds!"
        )


class ConflictingKeyBindError(CharmException):
    def __init__(self, keyname: str, action_name: str):
        super().__init__(
            title="Key bound to multiple conflicting actions!",
            message=f"Key '{keyname}' has multiple actions assigned! ({action_name})"
        )


class MissingRequiredKeyBindError(CharmException):
    def __init__(self, action: str):
        super().__init__("Action unbound!", f"Action '{action}' not bound to a key!")


class ScoreDBVersionMismatchError(CharmException):
    def __init__(self, version: str, correct_version: str):
        super().__init__("Score DB version mismatch!", f"Version {version} mismatched with correct version {correct_version}!")


class InvalidNoteLengthError(CharmException):
    def __init__(self, length: float, body_length: float):
        super().__init__("Invalid Note Length!", f"The note is trying to be {length} but this makes the note's body {body_length} long.", "warning")
