import importlib.resources as pkg_resources

from charm.lib.gamemodes.four_key import FourKeySong
import charm.data.tests


def test_4k():
    song = FourKeySong.parse(pkg_resources.path(charm.data.tests, "discord"))
    assert song.charts is not []
