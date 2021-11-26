pragma solidity 0.5.7;
// Copyright BigchainDB GmbH and Ocean Protocol contributors
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
// Code is Apache-2.0 and docs are CC-BY-4.0

import '../interfaces/IERC20Template.sol';



contract Dispenser {
    struct DataToken {
        bool active;  // if the dispenser is active for this datatoken
        address owner; // owner of this dispenser
        bool minterApproved; // if the dispenser is a minter for this datatoken
        uint256 maxTokens; // max tokens to dispense
        uint256 maxBalance; // max balance of requester. 
        //If the balance is higher, the dispense is rejected
    }
    mapping(address => DataToken) datatokens;
    address[] public datatokensList;
    constructor() public {}
    
    event Activated(  // emited when a dispenser is activated
        address indexed datatokenAddress
    );

    event Deactivated( // emited when a dispenser is deactivated
        address indexed datatokenAddress
    );

    event AcceptedMinter( 
        // emited when a dispenser becomes minter of the datatoken
        address indexed datatokenAddress
    );

    event RemovedMinter( 
        // emited when a dispenser if removed as minter of the datatoken
        address indexed datatokenAddress
    );

    event TokensDispensed( 
        // emited when tokens are dispended
        address indexed datatokenAddress,
        address indexed userAddress,
        uint256 amount
    );

    event OwnerWithdrawed(
        address indexed datatoken,
        address indexed owner,
        uint256 amount
    );

    /**
     * @dev status
     *      Get information about a datatoken dispenser
     * @param datatoken refers to datatoken address.
     * @return active - if the dispenser is active for this datatoken
     * @return owner - owner of this dispenser
     * @return minterApproved - if the dispenser is a minter for this datatoken
     * @return isTrueMinter  - check the datatoken contract if this contract is really a minter
     * @return maxTokens - max tokens to dispense
     * @return maxBalance - max balance of requester. If the balance is higher, the dispense is rejected
     * @return balance - internal balance of the contract (if any)
     */
    function status(address datatoken) 
    external view 
    returns(bool active,address owner,bool minterApproved,
    bool isTrueMinter,uint256 maxTokens,uint256 maxBalance, uint256 balance){
        require(
            datatoken != address(0),
            'Invalid token contract address'
        );
        active = datatokens[datatoken].active;
        owner = datatokens[datatoken].owner;
        minterApproved = datatokens[datatoken].minterApproved;
        maxTokens = datatokens[datatoken].maxTokens;
        maxBalance = datatokens[datatoken].maxBalance;
        IERC20Template tokenInstance = IERC20Template(datatoken);
        balance = tokenInstance.balanceOf(address(this));
        isTrueMinter = tokenInstance.isMinter(address(this));
    }

    /**
     * @dev activate
     *      Activate a new dispenser
     * @param datatoken refers to datatoken address.
     * @param maxTokens - max tokens to dispense
     * @param maxBalance - max balance of requester.
     */
    function activate(address datatoken,uint256 maxTokens, uint256 maxBalance)
        external {
        require(
            datatoken != address(0),
            'Invalid token contract address'
        );
        require(
            datatokens[datatoken].owner == address(0) || datatokens[datatoken].owner == msg.sender,
            'DataToken already activated'
        );
        IERC20Template tokenInstance = IERC20Template(datatoken);
        require(
            tokenInstance.isMinter(msg.sender),
            'Sender does not have the minter role'
        );
        datatokens[datatoken].active = true;
        datatokens[datatoken].owner = msg.sender;
        datatokens[datatoken].maxTokens = maxTokens;
        datatokens[datatoken].maxBalance = maxBalance;
        datatokens[datatoken].minterApproved = false;
        datatokensList.push(datatoken);
        emit Activated(datatoken);
    }

    /**
     * @dev deactivate
     *      Deactivate an existing dispenser
     * @param datatoken refers to datatoken address.
     */
    function deactivate(address datatoken) external{
        require(
            datatoken != address(0),
            'Invalid token contract address'
        );
        require(
            datatokens[datatoken].owner == msg.sender,
            'DataToken already activated'
        );
        datatokens[datatoken].active = false;
        emit Deactivated(datatoken);
    }

    /**
     * @dev acceptMinter
     *      Accepts Minter role  (existing datatoken minter has to call datatoken.proposeMinter(dispenserAddress) first)
     * @param datatoken refers to datatoken address.
     */
    function acceptMinter(address datatoken) external{
        require(
            datatoken != address(0),
            'Invalid token contract address'
        );
        IERC20Template tokenInstance = IERC20Template(datatoken);
        tokenInstance.approveMinter();
        require(
            tokenInstance.isMinter(address(this)),
            'ERR: Cannot accept minter role'
        );
        datatokens[datatoken].minterApproved = true;
        emit AcceptedMinter(datatoken);
    }
    /**
     * @dev removeMinter
     *      Removes Minter role and proposes the owner as a new minter (the owner has to call approveMinter after this)
     * @param datatoken refers to datatoken address.
     */
    function removeMinter(address datatoken) external{
        require(
            datatoken != address(0),
            'Invalid token contract address'
        );
        require(
            datatokens[datatoken].owner == msg.sender,
            'DataToken already activated'
        );
        IERC20Template tokenInstance = IERC20Template(datatoken);
        require(
            tokenInstance.isMinter(address(this)),
            'ERR: Cannot accept minter role'
        );
        tokenInstance.proposeMinter(datatokens[datatoken].owner);
        datatokens[datatoken].minterApproved = false;
        emit RemovedMinter(datatoken);
    }

    /**
     * @dev dispense
     *      Dispense datatokens to caller. The dispenser must be active, hold enough DT (or be able to mint more) and respect maxTokens/maxBalance requirements
     * @param datatoken refers to datatoken address.
     * @param datatoken amount of datatokens required.
     */
    function dispense(address datatoken, uint256 amount) external payable{
        require(
            datatoken != address(0),
            'Invalid token contract address'
        );
        require(
            datatokens[datatoken].active == true,
            'Dispenser not active'
        );
        require(
            amount > 0,
            'Invalid zero amount'
        );
        require(
            datatokens[datatoken].maxTokens >= amount,
            'Amount too high'
        );
        IERC20Template tokenInstance = IERC20Template(datatoken);
        uint256 callerBalance = tokenInstance.balanceOf(msg.sender);
        require(
            callerBalance<datatokens[datatoken].maxBalance,
            'Caller balance too high'
        );
        uint256 ourBalance = tokenInstance.balanceOf(address(this));
        if(ourBalance<amount && tokenInstance.isMinter(address(this))){ 
            //we need to mint the difference if we can
            tokenInstance.mint(address(this),amount - ourBalance);
            ourBalance = tokenInstance.balanceOf(address(this));
        }
        require(
            ourBalance>=amount,
            'Not enough reserves'
        );
        tokenInstance.transfer(msg.sender,amount);
        emit TokensDispensed(datatoken, msg.sender, amount);
    }

    /**
     * @dev ownerWithdraw
     *      Allow owner to withdraw all datatokens in this dispenser balance
     * @param datatoken refers to datatoken address.
     */
    function ownerWithdraw(address datatoken) external{
        require(
            datatoken != address(0),
            'Invalid token contract address'
        );
        require(
            datatokens[datatoken].owner == msg.sender,
            'Invalid owner'
        );
        IERC20Template tokenInstance = IERC20Template(datatoken);
        uint256 ourBalance = tokenInstance.balanceOf(address(this));
        if(ourBalance>0){
            tokenInstance.transfer(msg.sender,ourBalance);
            emit OwnerWithdrawed(datatoken, msg.sender, ourBalance);
        }
    }
    function() external payable {
        //thank you for your donation
    }
}