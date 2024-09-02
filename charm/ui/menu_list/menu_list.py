from arcade import LRBT

from charm.lib.mini_mint import Element, VerticalElementList

from charm.ui.menu_list.chartset_element import ChartsetElement

from charm.refactor.generic import ChartSet, Chart, ChartMetadata, ChartSetMetadata

# -- TEMP --
from arcade import draw_text


class UnifiedChartsetMenuElement(Element[VerticalElementList]):

    def __init__(self, chartsets: list[ChartSet] = None, min_element_size: float = 100, element_padding: int = 2, left_fraction: float = 0.0, right_fraction: float = 1.0):
        super().__init__()
        self.min_element_size: float = min_element_size  # uses this to estimate the number of needed elements to simulate the full list
        self.element_padding: int = element_padding  # uses this to make sure the full list illusion isn't broken

        self.left_fraction: float = left_fraction  # How far from the left side of the region to start the bounds.
        self.right_fraction: float = right_fraction  # How far from the left side of the region to end the bounds.

        self.chartsets: list[ChartSet] = []

        self.highlighted_set_idx: int = 0
        self.set_scroll: float = 0.0
        self.highlighted_chart_idx: int = 0
        self.chart_scroll: float = 0.0
        self.current_selected_chartset: ChartSet = None
        self.current_selected_chart: ChartMetadata = None

        self.shown_sets: dict[ChartSetMetadata, ChartsetElement] = {}

        self.element_list: VerticalElementList[ChartsetElement] = VerticalElementList(strict=False)
        self.add_child(self.element_list)

        if chartsets:
            self.set_chartsets(chartsets)

        self.layout(force=True)

    def set_chartsets(self, chartsets: list[ChartSet]) -> None:
        self.chartsets = chartsets
        self.highlighted_set_idx = 0
        self.highlighted_chart_idx = 0
        self.current_selected_chartset = None
        self.current_selected_chart = None
        self._place_chartset_elements()
        self.invalidate_layout()

    def _place_chartset_elements(self) -> None:
        self.element_list.empty()
        if not self.chartsets:
            return
        v = self.bounds.height
        vh = v / 2.0

        half_count = int(vh // self.min_element_size) + self.element_padding

        # TODO: THIS MAKES THE ASSUMPTION THE SONG INDEX IS ALWAYS VALID
        # If this breaks sowwy :3
        start_idx = int(self.set_scroll)

        shown_sets = self.shown_sets
        next_songs = {}

        chartset = self.chartsets[start_idx]
        center = shown_sets.get(chartset.metadata, None)
        if center is None:
            center = ChartsetElement(self.min_element_size, chartset)
        if chartset == self.current_selected_chartset:
            center.select()
        next_songs[chartset.metadata] = center
        self.element_list.add_child(center)

        for offset in range(half_count):
            above_song = None if start_idx - offset - 1 < 0 else self.chartsets[start_idx - offset - 1]
            if above_song:
                above_element = shown_sets.get(above_song.metadata, None)
                if above_element is None:
                    above_element = ChartsetElement(self.min_element_size, above_song)
                next_songs[above_song.metadata] = above_element
            else:
                above_element = ChartsetElement(self.min_element_size)
            self.element_list.insert_child(above_element, 0)
            if above_song == self.current_selected_chartset and above_element.chartset is not None:
                above_element.select()

            post_song = None if start_idx + offset + 1 >= len(self.chartsets) else self.chartsets[start_idx + offset + 1]
            if post_song:
                post_element = shown_sets.get(post_song.metadata, None)
                if post_element is None:
                    post_element = ChartsetElement(self.min_element_size, post_song)
                next_songs[post_song.metadata] = post_element
            else:
                post_element =ChartsetElement(self.min_element_size)
            self.element_list.add_child(post_element)
            if post_song == self.current_selected_chartset and post_element.chartset is not None:
                post_element.select()

        self.shown_sets = next_songs

    def _calc_layout(self) -> None:
        self.set_scroll = self.highlighted_set_idx
        self.chart_scroll =  self.highlighted_chart_idx

        v = self.bounds.height
        vh = v / 2.0

        half_count = int(vh // self.min_element_size) + self.element_padding
        v_count = half_count + 0.5
        top = self.bounds.y + v_count * self.min_element_size
        bot = self.bounds.y - v_count * self.min_element_size
        lef = self.bounds.left + self.left_fraction * self.bounds.width
        rig = self.bounds.left + self.right_fraction * self.bounds.width

        self._place_chartset_elements()

        # Idx scroll

        # Sub scroll
        # TODO: The 45.0 here is hard coded which is gross af. so is that 20.0 initial offset, both should depend on the size of the chart elements.
        sub_scroll = (self.current_selected_chartset is not None and (self.min_element_size / 2 + 20.0)) + 45.0 * self.chart_scroll

        # The menu list works with the children's minimum size to figure out the needed offset
        centering_offset = sum(child.minimum_size.y for child in self.element_list.children[:half_count]) - (half_count * self.min_element_size)

        self.element_list.bounds = LRBT(lef, rig, bot + centering_offset + sub_scroll, top + centering_offset + sub_scroll)

    def select_set(self, chartset: ChartSet):
        if self.current_selected_chartset is not None and self.current_selected_chartset.metadata in self.shown_sets:
            self.shown_sets[self.current_selected_chartset.metadata].deselect()

        self.current_selected_chartset = chartset
        self.highlighted_chart_idx = 0
        self.invalidate_layout()

        if chartset.metadata in self.shown_sets:
            self.shown_sets[chartset.metadata].select()
        #TODO: If the song element doesn't exist, delay the opening, or track that it needs to happen at creation

    def select_chart(self, chart: ChartMetadata):
        self.current_selected_chart = chart
        self.invalidate_layout()
        #TODO: load chart?

    def select_chart_element(self, element):
        print('not yet implimented internally')

    def select_currently_highlighted(self):
        self.invalidate_layout()
        if self.current_selected_chartset is None:
            self.select_set(self.chartsets[self.highlighted_set_idx])
            return
        self.select_chart(self.current_selected_chartset.charts[self.highlighted_chart_idx])

    def _down_sub_scroll(self, count: int):
        self.highlighted_chart_idx += count

        if self.highlighted_chart_idx < len(self.current_selected_chartset.charts):
            return

        # We are outside the chartsets list of charts, so lets close it
        if self.current_selected_chartset.metadata in self.shown_sets:
            self.shown_sets[self.current_selected_chartset.metadata].deselect()
        self.current_selected_chart = None
        self.current_selected_chartset = None
        self.highlighted_chart_idx = 0
        # TODO: Toggle the current song element

        self._down_scroll(count=1)

    def _down_scroll(self, count: int):
        if not self.chartsets:
            return
        self.highlighted_set_idx = (self.highlighted_set_idx + count) % len(self.chartsets)

    def down_scroll(self, count: int = 1):
        self.invalidate_layout()
        if self.current_selected_chartset is not None:
            self._down_sub_scroll(count=count)
            return
        self._down_scroll(count=count)

    def _up_sub_scroll(self, count: int):
        self.highlighted_chart_idx -= count

        if self.highlighted_chart_idx >= 0:
            return

        # We are outside the chartsets list of charts, so lets close it
        if self.current_selected_chartset.metadata in self.shown_sets:
            self.shown_sets[self.current_selected_chartset.metadata].deselect()
        self.current_selected_chart = None
        self.current_selected_chartset = None
        self.highlighted_chart_idx = 0
        # TODO: Toggle the current song element

    def _up_scroll(self, count: int):
        if not self.chartsets:
            return
        self.highlighted_set_idx = (self.highlighted_set_idx - count) % len(self.chartsets)

    def up_scroll(self, count: int = 1):
        self.invalidate_layout()
        if self.current_selected_chartset is not None:
            self._up_sub_scroll(count=count)
            return
        self._up_scroll(count=count)

    def _display(self) -> None:
        if self.current_selected_chartset is None:
            return

        draw_text(f"Chartset Metadata {self.current_selected_chartset.metadata}", self.bounds.right - 5.0, self.bounds.y, anchor_x='right', color=(0, 0, 0, 255))
