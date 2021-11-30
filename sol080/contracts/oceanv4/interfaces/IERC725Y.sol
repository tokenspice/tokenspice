// SPDX-License-Identifier: CC0-1.0
pragma solidity >=0.5.0 <0.9.0;

/**
 * @title ERC725 Y data store
 * @dev Contract module which provides the ability to set arbitrary key value sets that can be changed over time.
 * It is intended to standardise certain keys value pairs to allow automated retrievals and interactions
 * from interfaces and other smart contracts.
 *
 * ERC 165 interface id: 0x2bd57b73
 *
 * `setData` should only be callable by the owner of the contract set via ERC173.
 */
interface IERC725Y /* is ERC165, ERC173 */ {

    /**
    * @dev Emitted when data at a key is changed.
    */
    event DataChanged(bytes32 indexed key, bytes value);

    /**
     * @dev Gets data at a given `key`
     */
    function getData(bytes32 key) external view returns (bytes memory value);

    /**
     * @dev Sets data at a given `key`.
     * SHOULD only be callable by the owner of the contract set via ERC173.
     *
     * Emits a {DataChanged} event.
     */
   // function setData(bytes32 key, bytes calldata value) internal;
}