#code that's re-used by pytest modules

import pytest

_NETWORK = "ganache"

@pytest.fixture
def my_constant_value():
    return 11.0


@pytest.fixture
def network():
    return _NETWORK
