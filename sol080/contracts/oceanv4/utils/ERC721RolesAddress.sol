pragma solidity 0.8.10;
// Copyright BigchainDB GmbH and Ocean Protocol contributors
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
// Code is Apache-2.0 and docs are CC-BY-4.0

contract ERC721RolesAddress {
    mapping(address => Roles) internal permissions;

    address[] public auth;

    struct Roles {
        bool manager;
        bool deployERC20;
        bool updateMetadata;
        bool store;
    }

    

    function getPermissions(address user) public view returns (Roles memory) {
        return permissions[user];
    }

     modifier onlyManager() {
        require(
            permissions[msg.sender].manager == true,
            "ERC721RolesAddress: NOT MANAGER"
        );
        _;
    }

    event AddedTo725StoreList(
        address indexed user,
        address indexed signer,
        uint256 timestamp,
        uint256 blockNumber
    );
    event RemovedFrom725StoreList(
        address indexed user,
        address indexed signer,
        uint256 timestamp,
        uint256 blockNumber
    );

    function addTo725StoreList(address _allowedAddress) public onlyManager {
        Roles storage user = permissions[_allowedAddress];
        user.store = true;
        auth.push(_allowedAddress);
        emit AddedTo725StoreList(_allowedAddress,msg.sender,block.timestamp,block.number);
    }

    function removeFrom725StoreList(address _allowedAddress) public {
        if(permissions[msg.sender].manager == true ||
        (msg.sender == _allowedAddress && permissions[msg.sender].store == true)
        ){
            Roles storage user = permissions[_allowedAddress];
            user.store = false;
            emit RemovedFrom725StoreList(_allowedAddress,msg.sender,block.timestamp,block.number);
        }
        else{
            revert("ERC721RolesAddress: Not enough permissions to remove from 725StoreList");
        }

    }


    event AddedToCreateERC20List(
        address indexed user,
        address indexed signer,
        uint256 timestamp,
        uint256 blockNumber
    );
    event RemovedFromCreateERC20List(
        address indexed user,
        address indexed signer,
        uint256 timestamp,
        uint256 blockNumber
    );
    function addToCreateERC20List(address _allowedAddress) public onlyManager {
        Roles storage user = permissions[_allowedAddress];
        user.deployERC20 = true;
        auth.push(_allowedAddress);
        emit AddedToCreateERC20List(_allowedAddress,msg.sender,block.timestamp,block.number);
    }

    //it's only called internally, so is without checking onlyManager
    function _addToCreateERC20List(address _allowedAddress) internal {
        Roles storage user = permissions[_allowedAddress];
        user.deployERC20 = true;
        auth.push(_allowedAddress);
        emit AddedToCreateERC20List(_allowedAddress,msg.sender,block.timestamp,block.number);
    }

    function removeFromCreateERC20List(address _allowedAddress)
        public
    {
        if(permissions[msg.sender].manager == true ||
        (msg.sender == _allowedAddress && permissions[msg.sender].deployERC20 == true)
        ){
            Roles storage user = permissions[_allowedAddress];
            user.deployERC20 = false;
            emit RemovedFromCreateERC20List(_allowedAddress,msg.sender,block.timestamp,block.number);
        }
        else{
            revert("ERC721RolesAddress: Not enough permissions to remove from ERC20List");
        }
    }

    event AddedToMetadataList(
        address indexed user,
        address indexed signer,
        uint256 timestamp,
        uint256 blockNumber
    );
    event RemovedFromMetadataList(
        address indexed user,
        address indexed signer,
        uint256 timestamp,
        uint256 blockNumber
    );
    function addToMetadataList(address _allowedAddress) public onlyManager {
        Roles storage user = permissions[_allowedAddress];
        user.updateMetadata = true;
        auth.push(_allowedAddress);
        emit AddedToMetadataList(_allowedAddress,msg.sender,block.timestamp,block.number);
    }
    //it's only called internally, so is without checking onlyManager
    function _addToMetadataList(address _allowedAddress) internal {
        Roles storage user = permissions[_allowedAddress];
        user.updateMetadata = true;
        auth.push(_allowedAddress);
        emit AddedToMetadataList(_allowedAddress,msg.sender,block.timestamp,block.number);
    }

    function removeFromMetadataList(address _allowedAddress)
        public
    {
        if(permissions[msg.sender].manager == true ||
        (msg.sender == _allowedAddress && permissions[msg.sender].updateMetadata == true)
        ){
            Roles storage user = permissions[_allowedAddress];
            user.updateMetadata = false;    
            emit RemovedFromMetadataList(_allowedAddress,msg.sender,block.timestamp,block.number);
        }
        else{
            revert("ERC721RolesAddress: Not enough permissions to remove from metadata list");
        }
    }

    event AddedManager(
        address indexed user,
        address indexed signer,
        uint256 timestamp,
        uint256 blockNumber
    );
    event RemovedManager(
        address indexed user,
        address indexed signer,
        uint256 timestamp,
        uint256 blockNumber
    );
    function _addManager(address _managerAddress) internal {
        Roles storage user = permissions[_managerAddress];
        user.manager = true;
        auth.push(_managerAddress);
        emit AddedManager(_managerAddress,msg.sender,block.timestamp,block.number);
    }

    function _removeManager(address _managerAddress) internal {
        Roles storage user = permissions[_managerAddress];
        user.manager = false;
        emit RemovedManager(_managerAddress,msg.sender,block.timestamp,block.number);
    }


    event CleanedPermissions(
        address indexed signer,
        uint256 timestamp,
        uint256 blockNumber
    );
    function _cleanPermissions() internal {
        for (uint256 i = 0; i < auth.length; i++) {
            Roles storage user = permissions[auth[i]];
            user.manager = false;
            user.deployERC20 = false;
            user.updateMetadata = false;
            user.store = false;
        }

        delete auth;
        emit CleanedPermissions(msg.sender,block.timestamp,block.number);
    }
}
