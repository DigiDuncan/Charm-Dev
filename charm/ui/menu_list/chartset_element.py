# Song element needs to take in song info and display it, and when selected they need to grow the chart sublist.
# The sublist can manage its on info, but it should be to update the styling of the song element and chart element.
from pyglet.math import Vec2
from arcade import Rect, LRBT
from charm.lib.charm import CharmColors
from charm.lib.mini_mint import Element, VerticalElementList, Padding, padded_sub_rect, Animation
from charm.lib.anim import ease_expoout, ease_quadinout
from charm.refactor.generic import ChartSet, ChartSetMetadata, Chart, ChartMetadata

# -- TEMP --
from arcade import draw, Text


class ChartElement(Element[Element]):
    # displays info about a specific chart and are spawned in the sublist of the SongListElement
    def __init__(self, padding: Padding = Padding(0, 0, 2.5, 2.5), min_height: float = 45.0):
        super().__init__(min_size=Vec2(0.0, min_height))
        self._padding: Padding = padding
        self._sub_region: Rect = padded_sub_rect(self.bounds, self._padding)
        self._chart: ChartMetadata = None
        self._text_obj: Text = None

    def set_chart(self, new_chart: ChartMetadata):
        self._chart = new_chart
        self.invalidate_layout()

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
        if self._text_obj is None:
            self._text_obj = Text('', 0.0, 0.0, (0, 0, 0, 255), anchor_x='center', anchor_y='center', font_name='bananaslip plus', font_size = 18)

        if self._chart is None:
            return

        self._text_obj.text = f'{self._chart.gamemode} - {self._chart.difficulty}' if self._sub_region.height > 15.0 else ''
        self._text_obj.position = self._sub_region.center

    def _display(self) -> None:
        draw.draw_rect_filled(self._sub_region, (255, 255, 255, 255))
        self._text_obj.draw()



class ChartsetDisplayElement(Element[Element]):
    # displays info about a specific chartset and are spawned by the ChartsetElement directly

    def __init__(self, padding: Padding = Padding(0, 0, 5, 5)):
        super().__init__()
        self._padding: Padding = padding
        self._sub_region: Rect = padded_sub_rect(self.bounds, self._padding)
        self._metadata: ChartSetMetadata = None
        self._text_obj: Text = None

    def set_metadata(self, new_data: ChartSetMetadata) -> None:
        self._metadata = new_data
        self.invalidate_layout()

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
        if self._text_obj is None:
            self._text_obj = Text('', 0.0, 0.0, (0, 0, 0, 255), anchor_x='left', anchor_y='center', font_name='bananaslip plus', font_size = 36)

        if self._metadata is None:
            return

        self._text_obj.text = f'{self._metadata.title}' if self._sub_region.height > 15.0 else ''
        self._text_obj.x = self._sub_region.left + 5  # TODO: Make this a variable
        self._text_obj.y = self._sub_region.center_y


    def _display(self) -> None:
        draw.draw_rect_filled(self._sub_region, CharmColors.FADED_PURPLE)
        self._text_obj.draw()


CHARTSET_ELEMENT_OPENING_SPEED = 0.5

class ChartsetElement(Element[ChartsetDisplayElement | VerticalElementList]):
    # Holds a SongElement and a sublist of ChartElements and manages how and when the sublist appears
    def __init__(self, min_height: float, chartset: ChartSet = None):
        super().__init__(Vec2(0.0, min_height))
        self._chartset: ChartSet = None
        self._min_height: float = min_height

        self._chartset_element: ChartsetDisplayElement = ChartsetDisplayElement()
        self.add_child(self._chartset_element)

        self._list_element: VerticalElementList[ChartElement] = VerticalElementList(strict=True)
        self.add_child(self._list_element)

        self._selected: bool = False
        self._decay: float = 16.0
        self._anim: Animation = None

        self.visible = False

        self.chartset = chartset

    def grow(self, fraction: float, elapsed: float) -> None:
        new_size = Vec2(0.0, 145.0 + fraction * (45.0 * (len(self._chartset.charts) - 1)))
        # TODO: make this better v
        if elapsed >= 0.3:
            new_size = Vec2(0.0, 145.0 + (45.0 * (len(self._chartset.charts) - 1)))
        self.minimum_size = new_size

        self.invalidate_layout()

    def shrink(self, fraction: float, elapsed: float):
        new_size = Vec2(0.0, 100.0 + (1 - fraction) * (45.0 * len(self._chartset.charts)))
        if elapsed >= CHARTSET_ELEMENT_OPENING_SPEED:
            new_size = Vec2(0.0, 100.0)
        self.minimum_size = new_size

        self.invalidate_layout()

    def cleanup(self, animiation: Animation):
        self._anim = None
        self.invalidate_layout()

    def select(self) -> None:
        if self._selected or self._chartset is None or not self._chartset.charts:
            return

        self._selected = True

        if self._anim is not None:
            Element.Animator.kill_animation(self._anim)
            self._anim = None

        self._list_element.empty()
        self._list_element.visible = True

        for chart in self._chartset.charts:
            elem = ChartElement()
            elem.set_chart(chart)
            self._list_element.add_child(elem)

        self._anim = self.start_animation(self.grow, CHARTSET_ELEMENT_OPENING_SPEED, function=ease_expoout, cleanup=self.cleanup)

    def deselect(self) -> None:
        if not self._selected:
            return

        self._selected = False

        if self._anim is not None:
            Element.Animator.kill_animation(self._anim)
            self._anim = None

        self._anim = self.start_animation(self.shrink, CHARTSET_ELEMENT_OPENING_SPEED, function=ease_expoout, cleanup=self.cleanup)

    def toggle(self) -> None:
        if self._selected:
            self.deselect()
            return
        self.select()

    def get_chart_element_from_idx(self, idx: int) -> ChartElement:
        if not self._list_element.children or idx >= len(self._list_element.children):
            raise ValueError(f"Invalid Index {idx} for element {self}")
        return self._list_element.children[idx]

    @property
    def chartset(self) -> ChartSet:
        return self._chartset

    @chartset.setter
    def chartset(self, new_set: ChartSet) -> None:
        if new_set == self._chartset:
            return

        self.visible = new_set is not None
        self._chartset = new_set
        if new_set is not None:
            self._chartset_element.set_metadata(new_set.metadata)
        self.invalidate_layout()

    def _calc_layout(self) -> None:
        l, r, b, t = self.bounds.lrbt
        self._chartset_element.bounds = LRBT(l, r, t - self._min_height, t)

        if (self._anim is None and not self._selected) or self.bounds.height < self._min_height + 40.0:
            self._list_element.empty()
            self._list_element.visible = False
        self._list_element.visible = True
        self._list_element.bounds = LRBT(l, r, b, t - self._min_height)