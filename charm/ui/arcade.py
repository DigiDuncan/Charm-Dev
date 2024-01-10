from pathlib import Path
from arcade.gui import UIManager, UIImage, UITextWidget, UIFlatButton, UIAnchorLayout
from charm.lib.charm import CharmColors

from charm.lib.digiview import DigiView
from charm.lib.generic.song import Metadata
from charm.ui.utils import get_album_art
from charm.lib.gamemodes.fnf import FNFSong
from charm.lib.paths import songspath

class SongButton(UIFlatButton):
    def __init__(self, metadata: Metadata, **kwargs):
        self.metadata = metadata
        super().__init__(text = metadata.title,
                         size_hint = (1/12, 1.0),
                         **kwargs)

def UIImage_from_metadata(metadata: Metadata) -> UIImage:
    t = get_album_art(metadata)
    return UIImage(t)

def UITextWidget_from_metadata(metadata: Metadata) -> UITextWidget:
    t = f"Artist: {metadata.artist}\nAlbum: {metadata.album}\nCharter: {metadata.charter}"
    return UITextWidget(t, True)

class SongMenuLayout(UIAnchorLayout):
    def __init__(self, metadatas: list[Metadata], **kwargs):
        super().__init__(**kwargs)
        self.metadatas = metadatas
        self.selected_index = 0
        self.add(
            UIImage_from_metadata(self.metadatas[self.selected_index]),
            anchor_x = "right",
            anchor_y = "top"
        )
        tw = UITextWidget_from_metadata(self.metadatas[self.selected_index])
        tw.place_text("left")
        self.add(tw,
            anchor_x = "left",
            anchor_y = "top"
        )

class ArcadeUITestView(DigiView):
    def __init__(self, *args, **kwargs):
        super().__init__(fade_in=0.5, bg_color=CharmColors.FADED_GREEN, *args, **kwargs)
        self.ui = UIManager()

        self.songs: list[Metadata] = []
        rootdir = Path(songspath / "fnf")
        dir_list = [d for d in rootdir.glob('**/*') if d.is_dir()]
        for d in dir_list:
            k = d.name
            for diff, suffix in [("expert", "-ex"), ("hard", "-hard"), ("normal", ""), ("easy", "-easy")]:
                if (d / f"{k}{suffix}.json").exists():
                    songdata = FNFSong.get_metadata(d)
                    self.songs.append(songdata)
                    break

        self.ui.add(SongMenuLayout(self.songs))

    def on_show_view(self):
        # Enable UIManager when view is shown to catch window events
        self.ui.enable()

    def on_hide_view(self):
        # Disable UIManager when view gets inactive
        self.ui.disable()

    def on_key_press(self, symbol: int, modifiers: int):
        return super().on_key_press(symbol, modifiers)

    def on_update(self, delta_time: float):
        return super().on_update(delta_time)

    def on_draw(self):
        self.clear()

        ...

        self.ui.draw()  # draws the UI on screen
