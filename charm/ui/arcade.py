from typing import Iterable, Optional
from pathlib import Path

from pyglet.event import EVENT_UNHANDLED

import arcade
from arcade.gui import UIManager, UIBoxLayout, UILabel, \
    UIFlatButton, UISpace, UIWidget, Property, Surface, bind, UIEvent, UIMouseDragEvent, UIMouseScrollEvent, \
    UIMouseEvent, UIImage, UIAnchorLayout
from charm.lib.charm import CharmColors
from charm.lib.digiview import DigiView
from charm.lib.generic.song import Metadata
from charm.ui.utils import get_album_art
from charm.lib.gamemodes.fnf import FNFSong
from charm.lib.paths import songspath

def UIFlatButton_from_metadata(metadata: Metadata) -> UIFlatButton:
    return UIFlatButton(text = metadata.title,
                        size_hint = (1/12, 1.0),
                        width = 300,
                        height = 10)

def UIImage_from_metadata(metadata: Metadata) -> UIImage:
    t = get_album_art(metadata)
    return UIImage(t)

def UILabel_from_metadata(metadata: Metadata) -> UILabel:
    t = f"Artist: {metadata.artist}\nAlbum: {metadata.album}\nCharter: {metadata.charter}"
    return UILabel(
        width = 1280/4,
        text = t,
        multiline = True,
        text_color = (0, 0, 0, 255)
    )

class SongMenuLayout(UIAnchorLayout):
    def __init__(self, metadatas: list[Metadata], **kwargs):
        super().__init__(**kwargs)
        self.metadatas = metadatas
        self.selected_index = 0
        self.sidebar = UIBoxLayout()
        self.sidebar.add(
            UIImage_from_metadata(self.metadatas[self.selected_index]))
        tw = UILabel_from_metadata(self.metadatas[self.selected_index])
        self.sidebar.add(tw)
        self.add(
            self.sidebar,
            anchor_x = "right",
            anchor_y = "top"
        )


# modified copy of arcade.gui.examples.scroll_area.py
class UIScrollArea(UIWidget):
    scroll_x = Property[float](default=0.0)
    scroll_y = Property[float](default=0.0)

    scroll_speed = 1.3
    invert_scroll = False

    def __init__(self, *,
                 x: float = 0, y: float = 0, width: float = 300, height: float = 300,
                 children: Iterable["UIWidget"] = tuple(),
                 size_hint=None,
                 size_hint_min=None,
                 size_hint_max=None,
                 canvas_size=(300, 300),
                 **kwargs):
        super().__init__(x=x, y=y, width=width, height=height, children=children, size_hint=size_hint,
                         size_hint_min=size_hint_min, size_hint_max=size_hint_max, **kwargs)
        self.surface = Surface(
            size=canvas_size,
        )

        bind(self, "scroll_x", self.trigger_full_render)
        bind(self, "scroll_y", self.trigger_full_render)

    def _do_render(self, surface: Surface, force=False) -> bool:
        if not self.visible:
            return False

        should_render = force or not self._rendered
        rendered = False

        with self.surface.activate():
            if should_render:
                self.surface.clear()

            if self.visible:
                for child in self.children:
                    rendered |= child._do_render(self.surface, should_render)

        if should_render or rendered:
            rendered = True
            self.do_render_base(surface)
            self.do_render(surface)
            self._rendered = True

        return rendered

    def do_render(self, surface: Surface):
        self.prepare_render(surface)
        # draw the whole surface, the scissor box, will limit the visible area on screen
        width, height = self.surface.size
        self.surface.position = (-self.scroll_x, -self.scroll_y)
        self.surface.draw((0, 0, width, height))

    def on_event(self, event: UIEvent) -> Optional[bool]:

        if isinstance(event, UIMouseDragEvent) and not self.rect.collide_with_point(event.x, event.y):
            return EVENT_UNHANDLED

        # drag scroll area around with middle mouse button
        if isinstance(event, UIMouseDragEvent) and event.buttons & arcade.MOUSE_BUTTON_MIDDLE:
            self.scroll_x -= event.dx
            self.scroll_y -= event.dy
            return True

        if isinstance(event, UIMouseScrollEvent):
            invert = -1 if self.invert_scroll else 1

            self.scroll_x -= event.scroll_x * self.scroll_speed * invert
            self.scroll_y -= event.scroll_y * self.scroll_speed * invert
            return True

        child_event = event
        if isinstance(event, UIMouseEvent):
            child_event = type(event)(**event.__dict__)  # type: ignore
            child_event.x = event.x - self.x + self.scroll_x
            child_event.y = event.y - self.y + self.scroll_y

        return super().on_event(child_event)


#      ┌───────────────────────────────────────────────────────────────────┐
#      │ ┌────────────────────────────────────────────┐ ┌────────────────┐ │
#      │ │ ┌─────────────────────────────────────┐    │ │┌───────────┐   │ │
#      │ │ │                Title                │    │ ││           │   │ │
#      │ │ └─────────────────────────────────────┘    │ ││           │   │ │
#      │ │ ┌─────────────────────────────────────┐    │ ││           │   │ │
#      │ │ │                Title                │    │ ││           │   │ │
#      │ │ └─────────────────────────────────────┘    │ │└───────────┘   │ │
#      │ │                                            │ │ Artist: ...    │ │
#      │ │                                            │ │ Album: ...     │ │
#      │ └────────────────────────────────────────────┘ └────────────────┘ │
#      └───────────────────────────────▲────────────────────────▲──────────┘
#                ▲                     │                        │
# ┌──────────────┴───────┐ ┌───────────┴──────────┐  ┌──────────┴───────────┐
# │   UIBoxLayout, use   │ │   scroll area with   │  │  vertical Boxlayout  │
# │   sizehint to grow   │ │   UIBoxLayout and    │  │   (IMG + multiline   │
# │  scroll area to 75%  │ │    UIFlatButtons     │  │        Label)        │
# └──────────────────────┘ └──────────────────────┘  └──────────────────────┘

class ArcadeUITestView(DigiView):
    def __init__(self, *args, **kwargs):
        super().__init__(fade_in=0.5, bg_color=CharmColors.FADED_GREEN, *args, **kwargs)

        self.ui = UIManager()
        self.ui.enable()

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

        root = UIBoxLayout(vertical=False, size_hint=(1, 1))  # horizontal layout
        root.with_padding(all=10)

        # setup the UIBoxLayout for the titles
        title_box = UIBoxLayout(
            vertical=True,
            space_between=5,
            width=300
        )
        for s in self.songs:
            # width and height have to be set, because the UIBoxLayout would shrink everything down to 0
            button = UIFlatButton_from_metadata(s)
            title_box.add(button)
        title_box.fit_content()  # resize the box to fit the content

        # scroll area for the titles, will take the available space
        title_scroll = UIScrollArea(size_hint=(0.75, 1), canvas_size=title_box.size)
        title_scroll.add(title_box)

        detail_box = UIBoxLayout(vertical=True, size_hint=(0.25, 1), space_between=10)  # holds the details
        detail_box.add(UIImage_from_metadata(self.songs[0]))
        detail_box.add(UILabel_from_metadata(self.songs[0]))

        # horizontal line
        self.spacer = UISpace(size_hint=(0, 0.9), size_hint_min=(2, 2), color=arcade.color.GRAY)

        # put everything together
        root.add(title_scroll)
        root.add(self.spacer)
        root.add(detail_box)
        self.ui.add(root)

        # bad workaround to scroll to the top
        # first we have to trigger do layout, so everything has the right size to calculate scrolling
        self.ui._do_layout()
        title_scroll.scroll_y = title_box.children[0].top - title_scroll.height

        self.debug = title_scroll

    def on_draw(self):
        arcade.start_render()
        self.ui.draw()
