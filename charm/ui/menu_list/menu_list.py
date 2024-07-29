from arcade import LRBT

from charm.lib.mini_mint import Element, VerticalElementList

from charm.ui.menu_list.song_element import SongListElement
from charm.ui.menu_list.song_stub import Song, Metadata, Chart


class SongMenuListElement(Element[VerticalElementList]):

    def __init__(self, songs: list[Song] = None, min_element_size: float = 100, element_padding: int = 2, left_fraction: float = 0.0, right_fraction: float = 1.0):
        super().__init__()
        self.min_element_size: float = min_element_size  # uses this to estimate the number of needed elements to simulate the full list
        self.element_padding: int = element_padding  # uses this to make sure the full list illusion isn't broken

        self.left_fraction: float = left_fraction  # How far from the left side of the region to start the bounds.
        self.right_fraction: float = right_fraction  # How far from the left side of the region to end the bounds.

        self.songs: list[Song] = songs or []

        self.element_list: VerticalElementList[SongListElement] = VerticalElementList(strict=False)
        self.add_child(self.element_list)

        self.layout(force=True)

    def set_songs(self, songs: list[Song]) -> None:
        self.songs = songs
        self.invalidate_layout()

    def _calc_layout(self) -> None:
        v = self.bounds.height
        vh = v / 2.0

        half_count = int(vh // self.min_element_size) + self.element_padding
        v_count = half_count + 0.5
        top = self.bounds.y + v_count * self.min_element_size
        bot = self.bounds.y - v_count * self.min_element_size
        lef = self.bounds.left + self.left_fraction * self.bounds.width
        rig = self.bounds.left + self.right_fraction * self.bounds.width

        curr_count = len(self.element_list.children)
        child_count = int(v_count*2)

        if curr_count == 0:
            # Since v_count as the 0.5 it will always be odd, and there should ways be atleast one.
            self.element_list.add_child(SongListElement(self.min_element_size))
            self.element_list.children[0].song = Song(Metadata('MIDDLE'), [Chart('fnf', 'yes') for _ in range(6)])
            curr_count += 1

        # TODO: optimise with pool maybe?
        if curr_count > child_count:
            for _ in range((curr_count - child_count) // 2):
                self.element_list.remove_child(self.element_list.children[0])
                self.element_list.remove_child(self.element_list.children[-1])
            # remove children
        elif curr_count < child_count:
            for _ in range((child_count - curr_count) // 2):
                start_element = SongListElement(self.min_element_size)
                start_element.song = Song(Metadata('AJKLSHDAJKLS'), [Chart('a', 'easy') for _ in range(_ + 3)])  # TODO: remove once scrolling is in
                self.element_list.insert_child(start_element, 0)
                end_element = SongListElement(self.min_element_size)
                end_element.song = Song(Metadata('asdklasdl'), [Chart('b', 'HARD >:)') for _ in range(_ + 2)])  # TODO: remove once scrolling is in
                self.element_list.add_child(end_element)
            # add children

        # The menu list works with the children's minimum size to figure out the needed offset
        centering_offset = sum(child.minimum_size.y for child in self.element_list.children[:half_count]) - (half_count * self.min_element_size)

        # Idx scroll

        # Sub scroll

        self.element_list.bounds = LRBT(lef, rig, bot + centering_offset, top + centering_offset)
