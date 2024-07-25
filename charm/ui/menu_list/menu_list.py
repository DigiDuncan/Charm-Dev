from arcade import Rect, LRBT

from charm.lib.mini_mint import Element, RegionElement, VerticalElementList
from charm.lib.generic.song import Song


class SongMenuListElement(Element[Element | None, VerticalElementList]):

    def __init__(self, parent: Element = None, songs: list[Song] = None, min_element_size: float = 100, element_padding: int = 2, left_fraction: float = 0.0, right_fraction: float = 1.0):
        super().__init__(parent)
        self.min_element_size: float = min_element_size  # uses this to estimate the number of needed elements to simulate the full list
        self.element_padding: int = element_padding  # uses this to make sure the full list illusion isn't broken

        self.left_fraction: float = left_fraction  # How far from the left side of the region to start the bounds.
        self.right_fraction: float = right_fraction  # How far from the left side of the region to end the bounds.

        self.songs: list[Song] = songs or []

        self.element_list: VerticalElementList = VerticalElementList()
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
        rig = self.bounds.left + self.right_fraction * self.bounds.height

        # Then calc the offset bassed on the children. This is a semi-recursive behaviour oh no O.o
