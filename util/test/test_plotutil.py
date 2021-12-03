from enforce_typing import enforce_types
import pytest

from util.plotutil import (
    YParam,
    _applyMult,
    _multUnitStr,
    _expandBOTHinY,
    LINEAR,
    LOG,
    BOTH,
    MULT1,
    MULT100,
    DIV1M,
    DIV1B,
    COUNT,
    DOLLAR,
    PERCENT,
)


@enforce_types
def test_yparam1():
    yparam = YParam(
        ["headername1", "headername2"],
        ["Header 1", "Header 2"],
        "Header 1 and 2",
        LINEAR,
        MULT1,
        COUNT,
    )

    assert yparam.y_header_names == ["headername1", "headername2"]
    assert yparam.labels == ["Header 1", "Header 2"]
    assert yparam.y_pretty_name == "Header 1 and 2"
    assert yparam.y_scale == LINEAR
    assert yparam.mult == MULT1
    assert yparam.unit == COUNT
    assert yparam.y_scale_str == "LINEAR"


def test_yparam2_yscale():
    for (y_scale, y_scale_str) in [(LINEAR, "LINEAR"), (LOG, "LOG"), (BOTH, "BOTH")]:

        yparam = YParam(["foo1"], ["foo 1"], "Foo 1", y_scale, MULT1, COUNT)
        assert yparam.y_scale == y_scale
        assert yparam.y_scale_str == y_scale_str

    BAD_VALUE = 99
    yparam = YParam(["foo1"], ["foo 1"], "Foo 1", BAD_VALUE, MULT1, COUNT)
    with pytest.raises(ValueError):
        yparam.y_scale_str  # pylint: disable=pointless-statement


@enforce_types
def test_applyMult():
    assert _applyMult([1.1, 1.201], MULT1) == [1.1, 1.201]

    assert pytest.approx(_applyMult([1.201], MULT1)[0]) == 1.201
    assert pytest.approx(_applyMult([1.201], MULT100)[0]) == 120.1
    assert pytest.approx(_applyMult([1.201], DIV1M)[0]) == 1.201e-6
    assert pytest.approx(_applyMult([1.201], DIV1B)[0]) == 1.201e-9


@enforce_types
def test_multUnitStr():
    assert _multUnitStr(MULT1, DOLLAR) == "$"
    assert _multUnitStr(DIV1M, DOLLAR) == "$M"
    assert _multUnitStr(DIV1B, DOLLAR) == "$B"
    assert _multUnitStr(MULT1, COUNT) == "count"
    assert _multUnitStr(DIV1M, COUNT) == "count, in millions"
    assert _multUnitStr(DIV1B, COUNT) == "count, in billions"
    assert _multUnitStr(MULT100, PERCENT) == "%"


def test_expandBOTHinY():
    yparams = [YParam(["foo1"], ["foo 1"], "Foo 1", BOTH, MULT1, COUNT)]
    yparams2 = _expandBOTHinY(yparams)
    assert len(yparams2) == 2
    assert sorted([yparams2[0].y_scale, yparams2[1].y_scale]) == sorted([LINEAR, LOG])


# not currently tested:
# _xyToPngs()
# csvToPngs()
