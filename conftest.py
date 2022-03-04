"""
Hooks to run commands after the entire testsuite or at_exit in unittest / pytest

https://stackoverflow.com/questions/62628825/hooks-to-run-commands-after-the-entire-testsuite-or-at-exit-in-unittest-pytest
"""
import pytest

import brownie


@pytest.fixture(scope="session", autouse=True)
def session_setup_teardown():
    # setup code goes here if needed
    yield
    cleanup_testsuite()


def cleanup_testsuite():
    if brownie.network.is_connected():
        brownie.network.disconnect()
