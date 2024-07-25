# Song element needs to take in song info and display it, and when selected they need to grow the chart sublist.
# The sublist can manage its on info, but it should be to update the styling of the song element and chart element.
from charm.lib.mini_mint import Element


class ChartElement(Element[Element | None, Element]):
    # displays info about a specific chart and are spawned in the sublist of the SongListElement
    pass


class SongElement(Element[Element | None, Element]):
    # displays info about a specific song and are spawned by the SongListElement directly
    pass


class SongListElement(Element[Element | None, Element]):
    # Holds a SongElement and a sublist of ChartElemetns and manages how and when the sublist appears
    pass
