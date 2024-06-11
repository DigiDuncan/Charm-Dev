from importlib.resources import files, as_file

from charm.lib.gamemodes.four_key import FourKeySong
import charm.data.tests


def test_4k() -> None:
    with as_file(files(charm.data.tests) / "discord") as path:
        song = FourKeySong.parse(path)
    assert song.charts is not []
