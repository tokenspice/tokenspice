pragma solidity >=0.6.0;

contract ERC20Roles {
    
   
    mapping(address => RolesERC20) public permissions;

    address[] public authERC20;

    struct RolesERC20 {
        bool minter;
        bool feeManager; 
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

    event AddedFeeManager(
        address indexed user,
        address indexed signer,
        uint256 timestamp,
        uint256 blockNumber
    );
    event RemovedFeeManager(
        address indexed user,
        address indexed signer,
        uint256 timestamp,
        uint256 blockNumber
    );
    function _addFeeManager(address _feeManager) internal {
        RolesERC20 storage user = permissions[_feeManager];
        require(user.feeManager == false, "ERC20Roles:  ALREADY A FEE MANAGER");
        user.feeManager = true;
        authERC20.push(_feeManager);
        emit AddedFeeManager(_feeManager,msg.sender,block.timestamp,block.number);
    }

    function _removeFeeManager(address _feeManager) internal {
        RolesERC20 storage user = permissions[_feeManager];
        user.feeManager = false;
        emit RemovedFeeManager(_feeManager,msg.sender,block.timestamp,block.number);
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
            user.feeManager = false;

        }
        
        delete authERC20;
        emit CleanedPermissions(msg.sender,block.timestamp,block.number);
        
    }
}
