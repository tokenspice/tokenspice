// SPDX-License-Identifier: Unknown
pragma solidity 0.8.10;


import "OpenZeppelin/openzeppelin-contracts@4.2.0/contracts/token/ERC20/ERC20.sol";

contract MockOcean is ERC20("Ocean","Ocean"){


    constructor(address owner) {
        _mint(owner, 1e23);
    }

}