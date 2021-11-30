// SPDX-License-Identifier: Unknown
pragma solidity ^0.8.0;


import "OpenZeppelin/openzeppelin-contracts@4.2.0/contracts/token/ERC20/ERC20.sol";

contract MockERC20 is ERC20{


    constructor(address owner, string memory name, string memory symbol) ERC20(name,symbol) {
        _mint(owner, 1e23);
    }

}