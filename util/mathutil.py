import logging
log = logging.getLogger('mathutil')

from math import log10, floor
import random
import re
import typing

from util.constants import INF
from util.strutil import StrMixin

def isNumber(x) -> bool:
    return isinstance(x, int) or isinstance(x, float)

def intInStr(s : str) -> int:
    int_s = re.sub("[^0-9]", "", s)
    return int(int_s)

class Range(StrMixin):
    def __init__(self, min_: float, max_: typing.Union[float,None]=None):
        assert (max_ is None) or (max_ >= min_)
        self.min_: float = min_
        self.max_: typing.Union[float, None] = max_

    def drawRandomPoint(self) -> float:
        if self.max_ is None:
            return self.min_
        else:
            return randunif(self.min_, self.max_)

def randunif(mn: float, mx: float) -> float:
    """Return a uniformly-distributed random number in range [mn, mx]"""
    assert mx >= mn
    if mn == mx:
        return mn
    else:
        return mn + random.random() * (mx - mn)

def round_sig(x: typing.Union[int,float], sig: int) -> typing.Union[int,float]:
    """Return a number with the specified # significant bits"""
    return round(x, sig-int(floor(log10(abs(x))))-1)
