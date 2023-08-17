import brownie

from util.constants import (
    INF,
    S_PER_MIN,
    S_PER_HOUR,
    S_PER_DAY,
    S_PER_WEEK,
    S_PER_MONTH,
    S_PER_YEAR,
)


def testINF():
    assert INF > 1.0


def testSeconds():
    assert (
        0 < S_PER_MIN < S_PER_HOUR < S_PER_DAY < S_PER_WEEK < S_PER_MONTH < S_PER_YEAR
    )
    assert S_PER_HOUR == (60 * 60)
    assert S_PER_WEEK == (60 * 60 * 24 * 7)
    assert S_PER_YEAR == (60 * 60 * 24 * 365)

    assert isinstance(S_PER_HOUR, int)
    assert isinstance(S_PER_DAY, int)
    assert isinstance(S_PER_WEEK, int)
    assert isinstance(S_PER_MONTH, int)
    assert isinstance(S_PER_YEAR, int)


def test_network_connected():
    """
    Importing from util.constants includes:
    brownie.network.connect("development")
    """
    assert brownie.network.is_connected()


def test_have_accounts():
    assert brownie.network.is_connected()
    # by default, brownie should have 10 accounts
    assert brownie.network.accounts
