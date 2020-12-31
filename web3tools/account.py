"""Accounts module."""

#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import eth_account # type: ignore[import]
import eth_utils
import eth_keys # type: ignore[import]
import logging
import os
import web3

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
    
    def keysStr(self):
        s = []
        s += [f"private key: {self.private_key}"]
        s += [f"address: {self.address}"]
        s += [""]
        return "\n".join(s)
    
def randomPrivateKey():
    return web3.eth.Account.create().key

def privateKeyToAddress(private_key: str) -> str:
    return eth_account.Account().from_key(private_key).address
