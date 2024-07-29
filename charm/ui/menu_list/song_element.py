# Song element needs to take in song info and display it, and when selected they need to grow the chart sublist.
# The sublist can manage its on info, but it should be to update the styling of the song element and chart element.
from pyglet.math import Vec2
from arcade import Rect, LRBT, clock
from charm.lib.mini_mint import Element, VerticalElementList, Padding, padded_sub_rect, Animation
from charm.lib.generic.song import Song
from charm.lib.anim import ease_expoout

# -- TEMP --
from arcade import draw


class ChartElement(Element[Element]):
    # displays info about a specific chart and are spawned in the sublist of the SongListElement
    def __init__(self, padding: Padding = Padding(0, 0, 5, 5)):
        super().__init__()
        self._padding: Padding = padding
        self._sub_region: Rect = padded_sub_rect(self.bounds, self._padding)

    @property
    def padding(self) -> Padding:
        return self._padding

    @padding.setter
    def padding(self, new_padding: Padding) -> None:
        if new_padding == self._padding:
            return

        self._padding = new_padding
        self.invalidate_layout()

    def _calc_layout(self) -> None:
        self._sub_region = padded_sub_rect(self.bounds, self._padding)

    def _display(self) -> None:
        draw.draw_rect_filled(self._sub_region, (255, 255, 255, 255))


class SongElement(Element[Element]):
    # displays info about a specific song and are spawned by the SongListElement directly

    def __init__(self, padding: Padding = Padding(0, 0, 5, 5)):
        super().__init__()
        self._padding: Padding = padding
        self._sub_region: Rect = padded_sub_rect(self.bounds, self._padding)

    @property
    def padding(self) -> Padding:
        return self._padding

    @padding.setter
    def padding(self, new_padding: Padding) -> None:
        if new_padding == self._padding:
            return

        self._padding = new_padding
        self.invalidate_layout()

    def _calc_layout(self) -> None:
        self._sub_region = padded_sub_rect(self.bounds, self._padding)

    def _display(self) -> None:
        draw.draw_rect_filled(self._sub_region, (255, 255, 255, 255))


class SongListElement(Element[SongElement | VerticalElementList]):
    # Holds a SongElement and a sublist of ChartElements and manages how and when the sublist appears
    def __init__(self, min_height: float):
        super().__init__(Vec2(0.0, min_height))
        self._song: Song = None

        self._song_element: SongElement = SongElement()
        self.add_child(self._song_element)

        self._list_element: VerticalElementList[ChartElement] = VerticalElementList()

        self._selected: bool = False
        self._decay: float = 16.0
        self._anim: Animation = None

    def grow(self, fraction: float, elapsed: float) -> None:
        new_size = Vec2(0.0, 200.0 + fraction * 300.0)
        # TODO: make this better v
        if elapsed >= 0.3:
            new_size = Vec2(0.0, 500.0)
        self.minimum_size = new_size

        print(new_size, elapsed)
        self.invalidate_layout()

    def shrink(self, fraction: float, elapsed: float):
        new_size = Vec2(0.0, 100.0 + (1 - fraction) * 400.0)
        if elapsed >= 0.3:
            new_size = Vec2(0.0, 100.0)
        self.minimum_size = new_size

        print(new_size)
        self.invalidate_layout()

    def select(self) -> None:
        if self._selected:
            return

        self._selected = True

        if self._anim is not None:
            Element.Animator.kill_animation(self._anim)
            self._anim = None

        self.start_animation(self.grow, 0.3, function=ease_expoout)

    def deselect(self) -> None:
        if not self._selected:
            return

        self._selected = False

        if self._anim is not None:
            Element.Animator.kill_animation(self._anim)
            self._anim = None

        self.start_animation(self.shrink, 0.3, function=ease_expoout)

    def toggle(self) -> None:
        if self._selected:
            self.deselect()
            return
        self.select()

    @property
    def song(self) -> Song:
        return self._song

    @song.setter
    def song(self, song: Song):
        if song == self._song:
            return

        self._song = song
        self.invalidate_layout()

    def _calc_layout(self) -> None:
        l, r, b, t = self.bounds.lrbt
        self._song_element.bounds = LRBT(l, r, t - self.minimum_size.y, t)

        if self.bounds.height <= self.minimum_size.y:
            self._list_element.visible = False
            self._list_element.bounds = LRBT(0, 0, 0, 0)
            return
        self._list_element.visible = True
        self._list_element.bounds = LRBT(l, r, b, t - self.minimum_size.y)
