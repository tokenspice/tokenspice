import configparser
import os

CONF_FILE_PATH = "./tokenspice.ini"


def confFileValue(section: str, key: str) -> str:
    conf = configparser.ConfigParser()
    path = os.path.expanduser(CONF_FILE_PATH)
    conf.read(path)
    return conf[section][key]
