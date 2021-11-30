from util import configutil


def test1():
    assert isinstance(configutil.CONF_FILE_PATH, str)
