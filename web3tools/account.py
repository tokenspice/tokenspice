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
    
    def __init__(self, private_key:str):
        self._private_key = private_key

    @property
    def private_key(self):
        return self._private_key

    @property
    def address(self):
        return privateKeyToAddress(self._private_key)

    @property
    def public_key(self):
        return privateKeyToPublicKey(self._private_key)
    
    def keysStr(self):
        s = []
        s += [f"private key: {self.private_key}"]
        s += [f"public key: {self.public_key}"]
        s += [f"address: {self.address}"]
        s += [""]
        return "\n".join(s)

def privateKeyToAddress(private_key: str) -> str:
    return eth_account.Account().from_key(private_key).address

def privateKeyToPublicKey(private_key: str):
    private_key_bytes = eth_utils.decode_hex(private_key)
    private_key_object = eth_keys.keys.PrivateKey(private_key_bytes)
    return private_key_object.public_key
