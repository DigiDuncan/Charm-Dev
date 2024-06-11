from importlib.resources import files, as_file

import pytest
from charm.lib.gamemodes.hero import HeroSong
import charm.data.tests

@pytest.fixture()
def soulless() -> HeroSong:
    with as_file(files(charm.data.tests) / "soulless5") as p:
        return HeroSong.parse(p)

def test_parse_soulless(soulless: HeroSong) -> None:
    assert soulless is not None

def test_soulless_chord_count(soulless: HeroSong) -> None:
    expert_chart = soulless.get_chart("Expert")
    assert expert_chart is not None
    assert len(expert_chart.chords) == 10699  # Known value

def test_soulless_metadata(soulless: HeroSong) -> None:
    assert soulless.metadata.title == "Soulless 5"  # Known values
    assert soulless.metadata.artist == "ExileLord"
    assert soulless.metadata.album == "Get Smoked"
    assert soulless.metadata.year == 2018
