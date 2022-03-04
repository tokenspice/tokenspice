pragma solidity 0.8.10;
// Copyright BigchainDB GmbH and Ocean Protocol contributors
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
// Code is Apache-2.0 and docs are CC-BY-4.0

contract ERC20Roles {
    
   
    mapping(address => RolesERC20) public permissions;

    address[] public authERC20;

    struct RolesERC20 {
        bool minter;
        bool paymentManager; 
    }

    event AddedMinter(
        address indexed user,
        address indexed signer,
        uint256 timestamp,
        uint256 blockNumber
    );
    event RemovedMinter(
        address indexed user,
        address indexed signer,
        uint256 timestamp,
        uint256 blockNumber
    );

    function getPermissions(address user) public view returns (RolesERC20 memory) {
        return permissions[user];
    }

    function _addMinter(address _minter) internal {
        RolesERC20 storage user = permissions[_minter];
        require(user.minter == false, "ERC20Roles:  ALREADY A MINTER");
        user.minter = true;
        authERC20.push(_minter);
        emit AddedMinter(_minter,msg.sender,block.timestamp,block.number);
    }

    function _removeMinter(address _minter) internal {
        RolesERC20 storage user = permissions[_minter];
        user.minter = false;
        emit RemovedMinter(_minter,msg.sender,block.timestamp,block.number);
    }

    event AddedPaymentManager(
        address indexed user,
        address indexed signer,
        uint256 timestamp,
        uint256 blockNumber
    );
    event RemovedPaymentManager(
        address indexed user,
        address indexed signer,
        uint256 timestamp,
        uint256 blockNumber
    );
    function _addPaymentManager(address _paymentCollector) internal {
        RolesERC20 storage user = permissions[_paymentCollector];
        require(user.paymentManager == false, "ERC20Roles:  ALREADY A FEE MANAGER");
        user.paymentManager = true;
        authERC20.push(_paymentCollector);
        emit AddedPaymentManager(_paymentCollector,msg.sender,block.timestamp,block.number);
    }

    function _removePaymentManager(address _paymentCollector) internal {
        RolesERC20 storage user = permissions[_paymentCollector];
        user.paymentManager = false;
        emit RemovedPaymentManager(_paymentCollector,msg.sender,block.timestamp,block.number);
    }


    

   
    event CleanedPermissions(
        address indexed signer,
        uint256 timestamp,
        uint256 blockNumber
    );

    
    function _cleanPermissions() internal {
        
        for (uint256 i = 0; i < authERC20.length; i++) {
            RolesERC20 storage user = permissions[authERC20[i]];
            user.minter = false;
            user.paymentManager = false;

        }
        
        delete authERC20;
        emit CleanedPermissions(msg.sender,block.timestamp,block.number);
        
    }
}
