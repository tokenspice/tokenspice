pragma solidity 0.8.10;
// Copyright BigchainDB GmbH and Ocean Protocol contributors
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
// Code is Apache-2.0 and docs are CC-BY-4.0

interface IV3ERC20 {

    function mint(address account, uint256 value) external;
    function minter() external view returns(address);    
    function name() external view returns (string memory);
    function symbol() external view returns (string memory);
    function decimals() external view returns (uint8);
    function cap() external view returns (uint256);
    function isMinter(address account) external view returns (bool);
    function isInitialized() external view returns (bool);
    function allowance(address owner, address spender)
        external
        view
        returns (uint256);
    function transferFrom(
        address from,
        address to,
        uint256 value
    ) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address to, uint256 value) external returns (bool);
    function proposeMinter(address newMinter) external;
    function approveMinter() external;
    
    
}
