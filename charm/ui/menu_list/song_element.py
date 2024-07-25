# Song element needs to take in song info and display it, and when selected they need to grow the chart sublist.
# The sublist can manage its on info, but it should be to update the styling of the song element and chart element.
from charm.lib.mini_mint import Element


class ChartElement(Element[Element | None, Element]):
    pass


class SongElement(Element[Element | None, Element]):
    pass


class SongListElement(Element[Element | None, Element]):
    pass
