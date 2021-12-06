// SPDX-License-Identifier: MIT

pragma solidity 0.8.10;

interface IMetadata {
    function create(
        address dataToken,
        bytes calldata flags,
        bytes calldata data
    ) external;

    function update(
        address dataToken,
        bytes calldata flags,
        bytes calldata data
    ) external;
}
