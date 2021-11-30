// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.0;

// interfaces
import "../../interfaces/IERC725X.sol";
import "../../interfaces/IERC725Y.sol";
// modules
import "OpenZeppelin/openzeppelin-contracts@4.2.0/contracts/utils/introspection/ERC165Storage.sol";

// libraries
import "OpenZeppelin/openzeppelin-contracts@4.2.0/contracts/utils/Create2.sol";
import "GNSPS/solidity-bytes-utils@0.8.0/contracts/BytesLib.sol";


/**
 * @title ERC725 X / ERC725 Y executor
 * @dev Implementation of a contract module which provides the ability to call arbitrary functions at any other smart contract and itself,
 * including using `delegatecall`, as well creating contracts using `create` and `create2`.
 * This is the basis for a smart contract based account system, but could also be used as a proxy account system.
 *
 * `execute` MUST only be called by the owner of the contract set via ERC173.
 *
 *  @author Fabian Vogelsteller <fabian@lukso.network>
 */
contract ERC725Ocean is ERC165Storage, IERC725X, IERC725Y  {

    bytes4 internal constant _INTERFACE_ID_ERC725X = 0x44c028fe;

    uint256 constant OPERATION_CALL = 0;
    uint256 constant OPERATION_DELEGATECALL = 1;
    uint256 constant OPERATION_CREATE2 = 2;
    uint256 constant OPERATION_CREATE = 3;

    bytes4 internal constant _INTERFACE_ID_ERC725Y = 0x2bd57b73;

    mapping(bytes32 => bytes) internal store;

   
    constructor() {
       

        _registerInterface(_INTERFACE_ID_ERC725X);
        _registerInterface(_INTERFACE_ID_ERC725Y);
    }

    /* Public functions */

    /**
     * @notice Executes any other smart contract. Is only callable by the owner.
     *
     *
     * @param _operation the operation to execute: CALL = 0; DELEGATECALL = 1; CREATE2 = 2; CREATE = 3;
     * @param _to the smart contract or address to interact with. `_to` will be unused if a contract is created (operation 2 and 3)
     * @param _value the value of ETH to transfer
     * @param _data the call data, or the contract data to deploy
     */
    function execute(uint256 _operation, address _to, uint256 _value, bytes calldata _data)
    internal
    {
        // emit event
        emit Executed(_operation, _to, _value, _data);

        uint256 txGas = gasleft() - 2500;

        // CALL
        if (_operation == OPERATION_CALL) {
            executeCall(_to, _value, _data, txGas);

        // DELEGATE CALL
        // TODO: risky as storage slots can be overridden, remove?
//        } else if (_operation == OPERATION_DELEGATECALL) {
//            address currentOwner = owner();
//            executeDelegateCall(_to, _data, txGas);
//            // Check that the owner was not overridden
//            require(owner() == currentOwner, "Delegate call is not allowed to modify the owner!");

        // CREATE
        } else if (_operation == OPERATION_CREATE) {
            performCreate(_value, _data);

        // CREATE2
        } else if (_operation == OPERATION_CREATE2) {
            bytes32 salt = BytesLib.toBytes32(_data, _data.length - 32);
            bytes memory data = BytesLib.slice(_data, 0, _data.length - 32);

            address contractAddress = Create2.deploy(_value, salt, data);

            emit ContractCreated(contractAddress);

        } else {
            revert("Wrong operation type");
        }
    }

    /* Internal functions */

    // Taken from GnosisSafe
    // https://github.com/gnosis/safe-contracts/blob/development/contracts/base/Executor.sol
    function executeCall(address to, uint256 value, bytes memory data, uint256 txGas)
    internal
    returns (bool success)
    {
        // solium-disable-next-line security/no-inline-assembly
        assembly {
            success := call(txGas, to, value, add(data, 0x20), mload(data), 0, 0)
        }
    }

    // Taken from GnosisSafe
    // https://github.com/gnosis/safe-contracts/blob/development/contracts/base/Executor.sol
    function executeDelegateCall(address to, bytes memory data, uint256 txGas)
    internal
    returns (bool success)
    {
        // solium-disable-next-line security/no-inline-assembly
        assembly {
            success := delegatecall(txGas, to, add(data, 0x20), mload(data), 0, 0)
        }
    }

    // Taken from GnosisSafe
    // https://github.com/gnosis/safe-contracts/blob/development/contracts/libraries/CreateCall.sol
    function performCreate(uint256 value, bytes memory deploymentData)
    internal
    returns (address newContract)
    {
        // solium-disable-next-line security/no-inline-assembly
        assembly {
            newContract := create(value, add(deploymentData, 0x20), mload(deploymentData))
        }
        require(newContract != address(0), "Could not deploy contract");
        emit ContractCreated(newContract);
    }


       /* Public functions */

    /**
     * @notice Gets data at a given `key`
     * @param _key the key which value to retrieve
     * @return _value The data stored at the key
     */
    function getData(bytes32 _key)
    public
    view
    override
    virtual
    returns (bytes memory _value)
    {
        return store[_key];
    }

    /**
     * @notice Sets data at a given `key`
     * @param _key the key which value to retrieve
     * @param _value the bytes to set.
     */
    function setData(bytes32 _key, bytes calldata _value)
    internal
    virtual
    {
        store[_key] = _value;
        emit DataChanged(_key, _value);
    }


}