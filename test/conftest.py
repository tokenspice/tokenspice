#code that's re-used by pytest modules

import pytest

_NETWORK = "ganache"

@pytest.fixture
def network():
    return _NETWORK
