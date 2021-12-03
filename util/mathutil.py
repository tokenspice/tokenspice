from math import log10, floor
import random
import re
from typing import Union

from enforce_typing import enforce_types

from util.strutil import StrMixin


def isNumber(x) -> bool:
    return isinstance(x, (int, float))


@enforce_types
def intInStr(s: str) -> int:
    int_s = re.sub("[^0-9]", "", s)
    return int(int_s)


@enforce_types
class Range(StrMixin):
    def __init__(self, min_: float, max_: Union[float, None] = None):
        assert (max_ is None) or (max_ >= min_)
        self.min_: float = min_
        self.max_: Union[float, None] = max_

    def drawRandomPoint(self) -> float:
        if self.max_ is None:
            return self.min_
        return randunif(self.min_, self.max_)


@enforce_types
def randunif(mn: float, mx: float) -> float:
    """Return a uniformly-distributed random number in range [mn, mx]"""
    assert mx >= mn
    if mn == mx:
        return mn
    return mn + random.random() * (mx - mn)


@enforce_types
def round_sig(x: Union[int, float], sig: int) -> Union[int, float]:
    """Return a number with the specified # significant bits"""
    return round(x, sig - int(floor(log10(abs(x)))) - 1)
