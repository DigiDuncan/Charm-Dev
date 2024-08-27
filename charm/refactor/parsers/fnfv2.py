# Welcome to my personal hell.
# "Oh, we'll just have all the FNF parsers in one object,"
# "I'm sure the difference between the engines isn't that bad!"
# Which is true! Except for when FNF team in their infinite wisdom
# decides it's high time for a version 2, well after an entire community
# got used to the first one and created a ton of content surrounding it,
# that is not only completely incompatible but works entirely differently.

# Ways this breaks our understanding of FNF:
# - A seperate metadata file is supplied
# - All diffculties are in one chart file*
# - *except remixes because those are in a different file and use different audio
# so they shouldn't even share a folder but they do
# - Information from the metadata file is required to parse the chart
# - Importantly for Charm, these new files are indistinguishable from the old style
# without first opening them

# Listen, man, I didn't want Charm to 50% FNF either; I keep having to focus on it
# because it throws the most curveballs.
# Well-defined chart formats for the win. I need to make my own at this point.

# Here we go.

import json
from pathlib import Path
from typing import TypedDict
from charm.refactor.charts.fnf import FNFChart
from charm.refactor.generic.chart import ChartMetadata
from charm.refactor.generic.parser import Parser

class SongFileJson(TypedDict):
    ...


class FNFParser(Parser[FNFChart]):
    @staticmethod
    def parse_metadata(path: Path) -> list[ChartMetadata]:
        stem = path.stem
        chart = path.parent / (stem + "-chart.json")
        meta = path.parent / (stem + "-metadata.json")
        return []

    @staticmethod
    def parse_chart(chart_data: ChartMetadata) -> list[FNFChart]:
        with open(chart_data.path) as p:
            j: SongFileJson = json.load(p)

        charts = []

        return charts