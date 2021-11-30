// SPDX-License-Identifier: CC0-1.0
pragma solidity >=0.5.0 <0.9.0;

/**
 * @dev Contract module which provides the ability to call arbitrary functions at any other smart contract and itself,
 * including using `delegatecall`, as well creating contracts using `create` and `create2`.
 * This is the basis for a smart contract based account system, but could also be used as a proxy account system.
 *
 * ERC 165 interface id: 0x44c028fe
 *
 * `execute` should only be callable by the owner of the contract set via ERC173.
 */
interface IERC725X  /* is ERC165, ERC173 */ {

    /**
    * @dev Emitted when a contract is created.
    */
    event ContractCreated(address indexed contractAddress);

    /**
    * @dev Emitted when a contract executed.
    */
    event Executed(uint256 indexed _operation, address indexed _to, uint256 indexed  _value, bytes _data);


    /**
     * @dev Executes any other smart contract.
     * SHOULD only be callable by the owner of the contract set via ERC173.
     *
     * Requirements:
     *
     * - `operationType`, the operation to execute. So far defined is:
     *     CALL = 0;
     *     DELEGATECALL = 1;
     *     CREATE2 = 2;
     *     CREATE = 3;
     *
     * - `data` the call data that will be used with the contract at `to`
     *
     * Emits a {ContractCreated} event, when a contract is created under `operationType` 2 and 3.
     */
   // function execute(uint256 operationType, address to, uint256 value, bytes calldata data) internal payable;
}
