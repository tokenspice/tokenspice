#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import configparser
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from assets.contracts import artifacts
from enforce_typing import enforce_types
from drivers_oceanv4.integer import Integer
from drivers_oceanv4.env_constants import ENV_CONFIG_FILE
from drivers_oceanv4.constants import GAS_LIMIT_DEFAULT

DEFAULT_NETWORK_HOST = "localhost"
DEFAULT_NETWORK_PORT = 8545
DEFAULT_NETWORK_URL = "http://localhost:8545"
DEFAULT_BLOCK_CONFIRMATIONS = 1
DEFAULT_NETWORK_NAME = "ganache"
DEFAULT_ADDRESS_FILE = ""
DEFAULT_METADATA_CACHE_URI = "http://localhost:5000"
METADATA_CACHE_URI = "https://aquarius.oceanprotocol.com"
DEFAULT_PROVIDER_URL = "http://localhost:8030"
DEFAULT_DOWNLOADS_PATH = "consume-downloads"
DEFAULT_TRANSACTION_TIMEOUT = 10 * 60  # 10 minutes

NAME_NETWORK_URL = "network"
NETWORK_NAME = "network_name"
NAME_CHAIN_ID = "chain_id"
NAME_ADDRESS_FILE = "address.file"
NAME_GAS_LIMIT = "gas_limit"
NAME_BLOCK_CONFIRMATIONS = "block_confirmations"
NAME_METADATA_CACHE_URI = "metadata_cache_uri"
NAME_AQUARIUS_URL = "aquarius.url"
NAME_PROVIDER_URL = "provider.url"
NAME_TRANSACTION_TIMEOUT = "transaction_timeout"

NAME_DATA_TOKEN_FACTORY_ADDRESS = "dtfactory.address"
NAME_BFACTORY_ADDRESS = "bfactory.address"
NAME_OCEAN_ADDRESS = "OCEAN.address"

NAME_PROVIDER_ADDRESS = "provider.address"
NAME_DOWNLOADS_PATH = "downloads.path"

SECTION_ETH_NETWORK = "eth-network"
SECTION_RESOURCES = "resources"

environ_names_and_sections = {
    NAME_DATA_TOKEN_FACTORY_ADDRESS: [
        "DATA_TOKEN_FACTORY_ADDRESS",
        "Data token factory address",
        SECTION_ETH_NETWORK,
    ],
    NAME_BFACTORY_ADDRESS: [
        "BFACTORY_ADDRESS",
        "BPool factory address",
        SECTION_ETH_NETWORK,
    ],
    NAME_OCEAN_ADDRESS: ["OCEAN_ADDRESS", "OCEAN address", SECTION_ETH_NETWORK],
    NAME_NETWORK_URL: ["OCEAN_NETWORK_URL", "Network URL", SECTION_ETH_NETWORK],
    NAME_BLOCK_CONFIRMATIONS: [
        "BLOCK_CONFIRMATIONS",
        "Block confirmations",
        SECTION_ETH_NETWORK,
    ],
    NAME_ADDRESS_FILE: [
        "ADDRESS_FILE",
        "Path to json file of deployed contracts addresses",
        SECTION_ETH_NETWORK,
    ],
    NAME_GAS_LIMIT: ["GAS_LIMIT", "Gas limit", SECTION_ETH_NETWORK],
    NAME_TRANSACTION_TIMEOUT: [
        "OCEAN_TRANSACTION_TIMEOUT",
        "Transaction timeout",
        SECTION_ETH_NETWORK,
    ],
    NAME_METADATA_CACHE_URI: [
        "METADATA_CACHE_URI",
        "Metadata Cache URI",
        SECTION_RESOURCES,
    ],
    NAME_PROVIDER_URL: [
        "PROVIDER_URL",
        "URL of data services provider",
        SECTION_RESOURCES,
    ],
    NAME_PROVIDER_ADDRESS: [
        "PROVIDER_ADDRESS",
        "Provider ethereum address",
        SECTION_RESOURCES,
    ],
}

deprecated_environ_names = {
    NAME_AQUARIUS_URL: ["AQUARIUS_URL", "Aquarius URL", SECTION_RESOURCES]
}

config_defaults = {
    "eth-network": {
        NAME_NETWORK_URL: DEFAULT_NETWORK_URL,
        NETWORK_NAME: DEFAULT_NETWORK_NAME,
        NAME_ADDRESS_FILE: DEFAULT_ADDRESS_FILE,
        NAME_GAS_LIMIT: GAS_LIMIT_DEFAULT,
        NAME_BLOCK_CONFIRMATIONS: DEFAULT_BLOCK_CONFIRMATIONS,
        NAME_TRANSACTION_TIMEOUT: DEFAULT_TRANSACTION_TIMEOUT,
    },
    "resources": {
        NAME_METADATA_CACHE_URI: DEFAULT_METADATA_CACHE_URI,
        NAME_PROVIDER_URL: DEFAULT_PROVIDER_URL,
        NAME_PROVIDER_ADDRESS: "",
        NAME_DOWNLOADS_PATH: DEFAULT_DOWNLOADS_PATH,
    },
}


class Config(configparser.ConfigParser):
    """Class to manage the ocean-lib configuration."""

    def __init__(
        self,
        filename: Optional[Union[Path, str]] = None,
        options_dict: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> None:
        """Initialize Config class.

        Options available:
        ```
        [eth-network]
        ; ethereum network url
        network = https://rinkeby.infura.io/v3/<your Infura project id>

        [resources]
        metadata_cache_uri = http://localhost:5000
        provider.url = http://localhost:8030
        ```
        :param filename: Path of the config file, str.
        :param options_dict: Python dict with the config, dict.
        :param kwargs: Additional args. If you pass text, you have to pass the plain text configuration.
        """
        # can not enforce types on entire class, since init can not be checked
        # using enforce_types
        configparser.ConfigParser.__init__(self)

        self.read_dict(config_defaults)
        self._web3_provider = None
        self._logger = logging.getLogger("config")

        if filename:
            self._logger.debug(f"Config: loading config file {filename}")
            with open(filename) as fp:
                text = fp.read()
                self.read_string(text)
        elif "text" in kwargs:
            self._logger.debug("Config: loading config file {filename}.")
            self.read_string(kwargs["text"])
        elif options_dict:
            self._logger.debug(f"Config: loading from dict {options_dict}")
            self.read_dict(options_dict)
        else:
            filename = os.getenv(ENV_CONFIG_FILE)
            if filename is None:
                raise ValueError(f'Config file envvar "{ENV_CONFIG_FILE}" is empty')
            self._logger.debug(f"Config: loading config file {filename}")
            with open(filename) as fp:
                text = fp.read()
                self.read_string(text)
        self._handle_and_validate_metadata_cache_uri()
        self._load_environ()

    @enforce_types
    def _handle_and_validate_metadata_cache_uri(self) -> None:
        metadata_cache_uri = self.get(
            SECTION_RESOURCES, NAME_METADATA_CACHE_URI, fallback=None
        )
        aquarius_url = self.get(SECTION_RESOURCES, NAME_AQUARIUS_URL, fallback=None)

        if aquarius_url:
            self._logger.warning(
                f"Config: {SECTION_RESOURCES}.{NAME_AQUARIUS_URL} option is deprecated. "
                f"Use {SECTION_RESOURCES}.{NAME_METADATA_CACHE_URI} instead."
            )

        # Fallback to aquarius.url
        if aquarius_url and metadata_cache_uri == DEFAULT_METADATA_CACHE_URI:
            self.set(SECTION_RESOURCES, NAME_METADATA_CACHE_URI, aquarius_url)
            self.remove_option(SECTION_RESOURCES, NAME_AQUARIUS_URL)
            aquarius_url = None

        if aquarius_url and metadata_cache_uri:
            raise ValueError(
                (
                    f"Both {SECTION_RESOURCES}.{NAME_METADATA_CACHE_URI} and "
                    f"{SECTION_RESOURCES}.{NAME_AQUARIUS_URL} options are set. "
                    f"Use only {SECTION_RESOURCES}.{NAME_METADATA_CACHE_URI} because "
                    f"{SECTION_RESOURCES}.{NAME_AQUARIUS_URL} is deprecated."
                )
            )

    @enforce_types
    def _load_environ(self) -> None:
        for option_name, environ_item in environ_names_and_sections.items():
            if option_name == NAME_METADATA_CACHE_URI:
                metadata_cache_uri = os.environ.get(environ_item[0])
                aquarius_url = os.environ.get(
                    deprecated_environ_names[NAME_AQUARIUS_URL][0]
                )

                if metadata_cache_uri and aquarius_url:
                    raise ValueError(
                        (
                            "Both METADATA_CACHE_URI and AQUARIUS_URL envvars are set. "
                            "Use only METADATA_CACHE_URI because AQUARIUS_URL is deprecated."
                        )
                    )

                if aquarius_url:
                    self._logger.warning(
                        "Config: AQUARIUS_URL envvar is deprecated. Use METADATA_CACHE_URI instead."
                    )

                # fallback to AQUARIUS_URL
                value = metadata_cache_uri if metadata_cache_uri else aquarius_url
            else:
                value = os.environ.get(environ_item[0])
            if value is not None:
                self._logger.debug(f"Config: setting environ {option_name} = {value}")
                self.set(environ_item[2], option_name, value)

    @property
    @enforce_types
    def address_file(self) -> str:
        file_path = self.get(SECTION_ETH_NETWORK, NAME_ADDRESS_FILE)
        if file_path:
            file_path = str(Path(file_path).expanduser().resolve())
        else:
            file_path = str(
                Path(artifacts.__file__)
                .parent.joinpath("address.json")
                .expanduser()
                .resolve()
            )

        return file_path

    @property
    @enforce_types
    def block_confirmations(self) -> Integer:
        """Block confirmations."""
        return Integer(int(self.get(SECTION_ETH_NETWORK, NAME_BLOCK_CONFIRMATIONS)))

    @property
    @enforce_types
    def transaction_timeout(self) -> Integer:
        """Transaction timeout."""
        return Integer(int(self.get(SECTION_ETH_NETWORK, NAME_TRANSACTION_TIMEOUT)))

    @property
    @enforce_types
    def network_url(self) -> str:
        """URL of the ethereum network. (e.g.): http://mynetwork:8545."""
        return self.get(SECTION_ETH_NETWORK, NAME_NETWORK_URL)

    @property
    @enforce_types
    def network_name(self) -> str:
        """Name of the ethereum network. (e.g.): ganache."""
        return self.get(SECTION_ETH_NETWORK, NETWORK_NAME)

    @property
    @enforce_types
    def chain_id(self) -> int:
        """Chain ID of the ethereum network. (e.g.): 1337."""
        return int(self.get(SECTION_ETH_NETWORK, NAME_CHAIN_ID))

    @property
    @enforce_types
    def gas_limit(self) -> int:
        """Ethereum gas limit."""
        return int(self.get(SECTION_ETH_NETWORK, NAME_GAS_LIMIT))

    @property
    @enforce_types
    def metadata_cache_uri(self) -> str:
        """URL of metadata cache component. (e.g.): http://myaquarius:5000."""
        return self.get(SECTION_RESOURCES, NAME_METADATA_CACHE_URI)

    @property
    @enforce_types
    def provider_url(self) -> str:
        return self.get(SECTION_RESOURCES, NAME_PROVIDER_URL)

    @property
    @enforce_types
    def provider_address(self) -> str:
        """Provider address (e.g.): 0x00bd138abd70e2f00903268f3db08f2d25677c9e.

        Ethereum address of service provider
        """
        return self.get(SECTION_RESOURCES, NAME_PROVIDER_ADDRESS)

    @property
    @enforce_types
    def downloads_path(self) -> str:
        """Path for the downloads of assets."""
        return self.get(SECTION_RESOURCES, "downloads.path")
