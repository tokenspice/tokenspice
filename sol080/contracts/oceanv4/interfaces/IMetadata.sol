// SPDX-License-Identifier: MIT

pragma solidity >=0.6.2 <0.9.0;

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
