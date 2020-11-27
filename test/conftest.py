#code that's re-used by pytest modules

import pytest

@pytest.fixture
def my_constant_value():
    return 11.0

