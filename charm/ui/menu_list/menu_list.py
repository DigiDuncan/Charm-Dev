from arcade import LRBT

from charm.lib.mini_mint import Element, VerticalElementList

from charm.ui.menu_list.song_element import SongListElement
from charm.ui.menu_list.song_stub import Song, Metadata, Chart

# -- TEMP --
from arcade import draw_text


class SongMenuListElement(Element[VerticalElementList]):

    def __init__(self, songs: list[Song] = None, min_element_size: float = 100, element_padding: int = 2, left_fraction: float = 0.0, right_fraction: float = 1.0):
        super().__init__()
        self.min_element_size: float = min_element_size  # uses this to estimate the number of needed elements to simulate the full list
        self.element_padding: int = element_padding  # uses this to make sure the full list illusion isn't broken

        self.left_fraction: float = left_fraction  # How far from the left side of the region to start the bounds.
        self.right_fraction: float = right_fraction  # How far from the left side of the region to end the bounds.

        self.songs: list[Song] = songs or []

        self.highlighted_song_idx: int = 0
        self.song_scroll: float = 0.0
        self.highlighted_chart_idx: int = 0
        self.chart_scroll: float = 0.0
        self.current_selected_song: Song = None
        self.current_selected_chart: Chart = None

        self.shown_songs: dict[str, SongListElement] = {}

        self.element_list: VerticalElementList[SongListElement] = VerticalElementList(strict=False)
        self.add_child(self.element_list)

        self.layout(force=True)

    def set_songs(self, songs: list[Song]) -> None:
        self.songs = songs
        self.highlighted_song_idx = 0
        self.highlighted_chart_idx = 0
        self.current_selected_song = None
        self.current_selected_chart = None
        self._place_song_elements()
        self.invalidate_layout()

    def _place_song_elements(self):
        self.element_list.empty()
        if not self.songs:
            return
        v = self.bounds.height
        vh = v / 2.0

        half_count = int(vh // self.min_element_size) + self.element_padding

        # TODO: THIS MAKES THE ASSUMPTION THE SONG INDEX IS ALWAYS VALID
        # If this breaks sowwy :3
        start_idx = int(self.song_scroll)

        shown_songs = self.shown_songs
        next_songs: dict[str, SongListElement] = {}

        c_song = self.songs[start_idx]
        center = shown_songs.get(c_song.data.name, SongListElement(self.min_element_size, c_song))
        next_songs[c_song.data.name] = center
        self.element_list.add_child(center)

        for offset in range(half_count):
            above_song = None if start_idx - offset - 1 < 0 else self.songs[start_idx - offset - 1]
            if above_song:
                above_element = shown_songs.get(above_song.data.name, SongListElement(self.min_element_size, above_song))
                next_songs[above_song.data.name] = above_element
            else:
                above_element = SongListElement(self.min_element_size)
            self.element_list.insert_child(above_element, 0)

            post_song = None if start_idx + offset + 1 >= len(self.songs) else self.songs[start_idx + offset + 1]
            if post_song:
                post_element = shown_songs.get(post_song.data.name, SongListElement(self.min_element_size, post_song))
                next_songs[post_song.data.name] = post_element
            else:
                post_element = SongListElement(self.min_element_size)
            self.element_list.add_child(post_element)

        self.shown_songs = next_songs

    def _calc_layout(self) -> None:
        self.song_scroll = self.highlighted_song_idx
        self.chart_scroll =  self.highlighted_chart_idx

        v = self.bounds.height
        vh = v / 2.0

        half_count = int(vh // self.min_element_size) + self.element_padding
        v_count = half_count + 0.5
        top = self.bounds.y + v_count * self.min_element_size
        bot = self.bounds.y - v_count * self.min_element_size
        lef = self.bounds.left + self.left_fraction * self.bounds.width
        rig = self.bounds.left + self.right_fraction * self.bounds.width

        self._place_song_elements()

        # Idx scroll

        # Sub scroll
        # TODO: The 45.0 here is hard coded which is gross af.
        sub_scroll = (self.current_selected_song is not None and (self.min_element_size / 2 + 20.0)) + 45.0 * self.chart_scroll

        # The menu list works with the children's minimum size to figure out the needed offset
        centering_offset = sum(child.minimum_size.y for child in self.element_list.children[:half_count]) - (half_count * self.min_element_size)

        self.element_list.bounds = LRBT(lef, rig, bot + centering_offset + sub_scroll, top + centering_offset + sub_scroll)

    def select_song(self, song: Song):
        if self.current_selected_song is not None and self.current_selected_song.data.name in self.shown_songs:
            self.shown_songs[self.current_selected_song.data.name].deselect()

        self.current_selected_song = song
        self.highlighted_chart_idx = 0
        self.invalidate_layout()

        if song.data.name in self.shown_songs:
            self.shown_songs[song.data.name].select()
        #TODO: If the song element doesn't exist, delay the opening, or track that it needs to happen at creation

    def select_chart(self, chart: Chart):
        self.current_selected_chart = chart
        self.invalidate_layout()
        #TODO: load chart?

    def select_chart_element(self, element):
        raise NotImplementedError

    def select_currently_highlighted(self):
        self.invalidate_layout()
        if self.current_selected_song is None:
            self.select_song(self.songs[self.highlighted_song_idx])
            return
        self.select_chart(self.current_selected_song.charts[self.highlighted_chart_idx])

    def _down_sub_scroll(self):
        self.highlighted_chart_idx += 1

        if self.highlighted_chart_idx < len(self.current_selected_song.charts):
            return

        # We are outside the chartsets list of charts, so lets close it
        if self.current_selected_song.data.name in self.shown_songs:
            self.shown_songs[self.current_selected_song.data.name].deselect()
        self.current_selected_chart = None
        self.current_selected_song = None
        self.highlighted_chart_idx = 0
        # TODO: Toggle the current song element

        self._down_scroll()

    def _down_scroll(self):
        self.highlighted_song_idx = (self.highlighted_song_idx + 1) % len(self.songs)

    def down_scroll(self):
        self.invalidate_layout()
        if self.current_selected_song is not None:
            self._down_sub_scroll()
            return
        self._down_scroll()

    def _up_sub_scroll(self):
        self.highlighted_chart_idx -= 1

        if self.highlighted_chart_idx >= 0:
            return

        # We are outside the chartsets list of charts, so lets close it
        if self.current_selected_song.data.name in self.shown_songs:
            self.shown_songs[self.current_selected_song.data.name].deselect()
        self.current_selected_chart = None
        self.current_selected_song = None
        self.highlighted_chart_idx = 0
        # TODO: Toggle the current song element

    def _up_scroll(self):
        self.highlighted_song_idx = (self.highlighted_song_idx - 1) % len(self.songs)

    def up_scroll(self):
        self.invalidate_layout()
        if self.current_selected_song is not None:
            self._up_sub_scroll()
            return
        self._up_scroll()

    def _display(self) -> None:
        return
        draw_text(
            f'highlighted song: {self.highlighted_song_idx} - {self.songs[self.highlighted_song_idx]}',
            self.bounds.right - 5.0, self.bounds.y, anchor_x='right', color=(0, 0, 0, 255)#
        )
        draw_text(
            f'selected song: {self.current_selected_song}',
            self.bounds.right - 5.0, self.bounds.y - 15.0, anchor_x='right', color=(0, 0, 0, 255)
        )
        c_chart_idx = None if self.current_selected_song is None else self.highlighted_chart_idx
        c_chart = None if self.current_selected_song is None else self.current_selected_song.charts[self.highlighted_chart_idx]
        draw_text(
            f'highlighted chart: {c_chart_idx} - {c_chart}',
            self.bounds.right - 5.0, self.bounds.y - 30.0, anchor_x='right', color=(0, 0, 0, 255)
        )
        draw_text(
            f'selected chart: {self.current_selected_chart}',
            self.bounds.right - 5.0, self.bounds.y - 45.0, anchor_x='right', color=(0, 0, 0, 255)
        )
