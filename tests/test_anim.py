import pytest

from charm.lib.anim import perc


@pytest.mark.parametrize(
    ("start", "end", "curr", "expected"),
    [
        (10, 20, 0, 0),
        (10, 20, 10, 0),
        (10, 20, 15, 0.5),
        (10, 20, 20, 1),
        (10, 20, 30, 1),
        (10, 10, 0, 0),
        (10, 10, 10, 1),
        (10, 10, 20, 1),
        (20, 10, 0, 0),
        (20, 10, 10, 0),
        (20, 10, 15, 0),
        (20, 10, 20, 1),
        (20, 10, 30, 1)
    ]
)
def test_find_percent(start: float, end: float, curr: float, expected: float) -> None:
    assert perc(start, end, curr) == expected
