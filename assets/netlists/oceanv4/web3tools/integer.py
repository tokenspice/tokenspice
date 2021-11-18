#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing.decorator import enforce_types


class Integer:
    @enforce_types
    def __init__(self, value: int) -> None:
        self.value = value
