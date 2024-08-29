from importlib.resources import files

import PIL, PIL.Image, PIL.ImageDraw  # noqa: E401
import arcade
from arcade import Sprite, Texture, color as colors

import charm.data.images.errors
from charm.lib.utils import img_from_path


class CharmError(Exception):
    _icon_textures: dict[str, Texture] = {}

    def __init__(self, *, title: str, message: str, icon: str = "error", repeat: int = 1):
        self.title = title
        self.message = message
        self.icon_name = icon
        self.repeat = repeat
        super().__init__(message)
        try:
            window = arcade.get_window()
        except RuntimeError:
            # If we aren't in an arcade Window (e.g., unit testing) we don't need the sprite stuff.
            return

        if icon not in CharmError._icon_textures:
            icon_img = img_from_path(files(charm.data.images.errors) / f"{self.icon_name}.png")
            icon_img.resize((32, 32), PIL.Image.LANCZOS)
            CharmError._icon_textures[icon] = Texture(icon_img)

        self._icon = CharmError._icon_textures[icon]
        self.sprite = self.get_sprite()
        self.sprite.position = (window.width / 2, window.height / 2)

    def redraw(self) -> None:
        window = arcade.get_window()
        self.sprite = self.get_sprite()
        self.sprite.position = (window.width / 2, window.height / 2)

    def get_sprite(self) -> Sprite:
        window = arcade.get_window()
        _tex = Texture.create_empty(f"_error-{self.title}-{self.message}", (500, 200))
        default_atlas = window.ctx.default_atlas
        default_atlas.add(_tex)

        sprite = Sprite(_tex)

        with default_atlas.render_into(_tex) as fbo:
            fbo.clear()

            arcade.draw_lrbt_rectangle_filled(0, 500, 0, 200, colors.BLANCHED_ALMOND)
            arcade.draw_lrbt_rectangle_filled(0, 500, 150, 200, colors.BRANDEIS_BLUE)
            arcade.draw_text(self.title + f"{' (' + str(self.repeat) + ')' if self.repeat > 1 else ''}", 50, 165, font_size=24, bold=True, font_name="bananaslip plus")
            arcade.draw_text(self.message, 5, 146, font_size=16, anchor_y="top", multiline=True, width=492, color=colors.BLACK, font_name="bananaslip plus")
            arcade.draw_texture_rect(self._icon, arcade.XYWH(25, 175, 32, 32))

        return sprite


class GenericError(CharmError):
    def __init__(self, error: Exception):
        super().__init__(title=error.__class__.__name__, message=str(error))


class TestError(CharmError):
    def __init__(self, message: str):
        super().__init__(title="Test", message=message)

class TODOError(CharmError):
    def __init__(self, person: str):
        super().__init__(title="TODO", message=f"{person} has to finish implementing/fixing this!", icon = "help")

class NoChartsError(CharmError):
    def __init__(self, song_name: str):
        super().__init__(title="No charts found!", message=f"No charts found for song '{song_name}'")


class NoMetadataError(CharmError):
    def __init__(self, song_name: str):
        super().__init__(title="No metadata found!", message=f"No metadata found for song '{song_name}'")

class MissingGamemodeError(CharmError):
    def __init__(self, *, gamemode: str):
        super().__init__(title="Gamemode not found!", message=f"{gamemode} has failed to initialise", icon="error")

class ChartParseError(CharmError):
    def __init__(self, line_num: int, message: str):
        super().__init__(title="Chart parsing error!", message=f"[Line {line_num}] {message}")


class MetadataParseError(CharmError):
    def __init__(self, message: str):
        super().__init__(title="Metadata parsing error!", message=message)

class ChartUnparseableError(CharmError):
    def __init__(self, message: str):
        super().__init__(title="Chart is unparsable", message=message, icon="error")

class ChartPostReadParseError(CharmError):
    def __init__(self, message: str):
        super().__init__(title="Chart post-read parse error!", message=message)


class UnknownLanesError(CharmError):
    def __init__(self, message: str):
        super().__init__(title="Unknown lanes found", message=message, icon="warning")


class TooManyKeyBindError(CharmError):
    def __init__(self, action: str):
        super().__init__(
            title="Too many key binds set!",
            message=f"Action '{action}' has too many key binds!"
        )


class ConflictingKeyBindError(CharmError):
    def __init__(self, keyname: str, action_name: str):
        super().__init__(
            title="Key bound to multiple conflicting actions!",
            message=f"Key '{keyname}' has multiple actions assigned! ({action_name})"
        )


class MissingRequiredKeyBindError(CharmError):
    def __init__(self, action: str):
        super().__init__(title="Action unbound!", message=f"Action '{action}' not bound to a key!")


class ScoreDBVersionMismatchError(CharmError):
    def __init__(self, version: str, correct_version: str):
        super().__init__(title="Score DB version mismatch!", message=f"Version {version} mismatched with correct version {correct_version}!")


class InvalidNoteLengthError(CharmError):
    def __init__(self, length: float, body_length: float):
        super().__init__(
            title="Invalid Note Length!",
            message=f"The note is trying to be {length} but this makes the note's body {body_length} long.",
            icon="warning"
        )


class NoSongsFoundError(CharmError):
    def __init__(self):
        super().__init__(
            title="No songs found!",
            message="Unable to load any songs into song menu."
        )
