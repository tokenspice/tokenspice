#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#


class OceanEncryptAssetUrlsError(Exception):
    """Error invoking the encrypt endpoint."""


class InsufficientBalance(Exception):
    """The token balance is insufficient."""


class ContractNotFound(Exception):
    """Contract address is not found in the factory events."""


class AquariusError(Exception):
    """Error invoking an Aquarius metadata service endpoint."""


class VerifyTxFailed(Exception):
    """Transaction verification failed."""


class TransactionFailed(Exception):
    """Transaction has failed."""
