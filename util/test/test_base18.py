from util.base18 import toBase18, fromBase18


def test_toBase18():
    # assert toBase18(1.23e6) == 1230000000000000000000000 #not quite
    assert toBase18(1.23) == 1230000000000000000
    assert toBase18(3e-18) == 3
    assert toBase18(1e-19) == 0


def test_fromBase18():
    assert fromBase18(1230000000000000000000000) == 1.23e6
    assert fromBase18(1230000000000000000) == 1.23
    assert fromBase18(3) == 3e-18
    assert fromBase18(0) == 0
