pragma solidity >=0.5.7;

interface IDispenser {
    
    function status(address datatoken) external view 
    returns(bool active,address owner,bool isMinter,uint256 maxTokens,uint256 maxBalance, uint256 balance);
    
    function create(
        address datatoken,uint256 maxTokens, uint256 maxBalance, address owner, address allowedSwapper) external;
    function activate(address datatoken,uint256 maxTokens, uint256 maxBalance) external;
    
    function deactivate(address datatoken) external;
    
    function dispense(address datatoken, uint256 amount, address destination) external;
    
    function ownerWithdraw(address datatoken) external;
    function setAllowedSwapper(address datatoken, address newAllowedSwapper) external;
}
