pragma solidity 0.5.7;
// Copyright BigchainDB GmbH and Ocean Protocol contributors
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
// Code is Apache-2.0 and docs are CC-BY-4.0

import './BPool.sol';
import './BConst.sol';
import '../utils/Deployer.sol';

/*
* @title BFactory contract
* @author Ocean Protocol (with code from Balancer Labs)
*
* @dev Ocean implementation of Balancer BPool Factory
*      BFactory deploys BPool proxy contracts.
*      New BPool proxy contracts are links to the template contract's bytecode.
*      Proxy contract functionality is based on Ocean Protocol custom
*        implementation of ERC1167 standard.
*/
contract BFactory is BConst, Deployer {

    address public bpoolTemplate;

    event BPoolCreated(
        address indexed newBPoolAddress,
        address indexed bpoolTemplateAddress
    );
    
    event BPoolRegistered(
        address bpoolAddress,
        address indexed registeredBy
    );
    
    /* @dev Called on contract deployment. Cannot be called with zero address.
       @param _bpoolTemplate -- address of a deployed BPool contract. */
    constructor(address _bpoolTemplate)
        public 
    {
        require(
            _bpoolTemplate != address(0), 
            'BFactory: invalid bpool template zero address'
        );
        bpoolTemplate = _bpoolTemplate;
    }

    /* @dev Deploys new BPool proxy contract.
       Template contract address could not be a zero address. 
       @return address of a new proxy BPool contract */
    function newBPool()
        external
        returns (address bpool)
    {
        bpool = deploy(bpoolTemplate);
        require(
            bpool != address(0), 
            'BFactory: invalid bpool zero address'
        );
        BPool bpoolInstance = BPool(bpool);	
        require(
            bpoolInstance.initialize(
                msg.sender,
                address(this), 
                MIN_FEE, 
                false,
                false
            ),
            'ERR_INITIALIZE_BPOOL'
        );
        emit BPoolCreated(bpool, bpoolTemplate);
        emit BPoolRegistered(bpool, msg.sender);
    }
}
