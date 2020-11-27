"""Accounts module."""

#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import eth_account
import eth_utils
import eth_keys
import logging
import os

logger = logging.getLogger('account')

class Account:
    """Class representing an account."""

    def __init__(self, address=None, password=None, key_file=None, encrypted_key=None, private_key=None):
        """
        Hold account address, password and either keyfile path, encrypted key or private key

        :param address: The address of this account
        :param password: account's password. This is necessary for decrypting the private key
            to be able to sign transactions locally
        :param key_file: str path to the encrypted private key file
        :param encrypted_key:
        :param private_key:
        """
        assert key_file or encrypted_key or private_key, \
            'Account requires one of `key_file`, `encrypted_key`, or `private_key`.'
        if key_file or encrypted_key:
            assert password, '`password` is required when using `key_file` or `encrypted_key`.'

        if private_key:
            password = None

        self.address = address
        self.password = password
        self._key_file = key_file
        if self._key_file and not encrypted_key:
            with open(self.key_file) as _file:
                encrypted_key = _file.read()
        self._encrypted_key = encrypted_key
        self._private_key = private_key

        if self.address is None and self._private_key is not None:
            self.address = privateKeyToAddress(private_key)
        
        assert self.address is not None

    @property
    def key_file(self):
        if self._key_file:
            return os.path.expandvars(os.path.expanduser(self._key_file))
        return None

    @property
    def private_key(self):
        return self._private_key

    @property
    def key(self):
        if self._private_key:
            return self._private_key

        return self._encrypted_key

    def keysStr(self):
        s = []
        s += [f"address: {self.address}"]
        if self._private_key is not None:
            s += [f"private key: {self._private_key}"]
            s += [f"public key: {privateKeyToPublicKey(self._private_key)}"]
        s += [""]
        return "\n".join(s)

def privateKeyToAddress(private_key: str) -> str:
    return eth_account.Account().from_key(private_key).address

def privateKeyToPublicKey(private_key: str):
    private_key_bytes = eth_utils.decode_hex(private_key)
    private_key_object = eth_keys.keys.PrivateKey(private_key_bytes)
    return private_key_object.public_key
