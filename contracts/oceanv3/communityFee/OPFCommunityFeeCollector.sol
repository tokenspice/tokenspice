pragma solidity ^0.5.7;
// Copyright BigchainDB GmbH and Ocean Protocol contributors
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
// Code is Apache-2.0 and docs are CC-BY-4.0
import '../interfaces/IERC20Template.sol';
import 'OpenZeppelin/openzeppelin-contracts@2.1.1/contracts/ownership/Ownable.sol';


/**
 * @title OPFCommunityFeeCollector
 * @dev Ocean Protocol Foundation Community Fee Collector contract
 *      allows consumers to pay very small fee as part of the exchange of 
 *      data tokens with ocean token in order to support the community of  
 *      ocean protocol and provide a sustainble development.
 */
contract OPFCommunityFeeCollector is Ownable {
    address payable private collector;
    /**
     * @dev constructor
     *      Called prior contract deployment. set the controller address and
     *      the contract owner address
     * @param newCollector the fee collector address.
     * @param OPFOwnerAddress the contract owner address
     */
    constructor(
        address payable newCollector,
        address OPFOwnerAddress
    ) 
        public
        Ownable()
    {
        require(
            newCollector != address(0)&&
            OPFOwnerAddress != address(0), 
            'OPFCommunityFeeCollector: collector address or owner is invalid address'
        );
        collector = newCollector;
        transferOwnership(OPFOwnerAddress);
    }
    /**
     * @dev fallback function
     *      this is a default fallback function in which receives
     *      the collected ether.
     */
    function() external payable {}

    /**
     * @dev withdrawETH
     *      transfers all the accumlated ether the collector address
     */
    function withdrawETH() 
        external 
        payable
    {
        collector.transfer(address(this).balance);
    }

    /**
     * @dev withdrawToken
     *      transfers all the accumlated tokens the collector address
     * @param tokenAddress the token contract address 
     */
    function withdrawToken(
        address tokenAddress
    ) 
        external
    {
        require(
            tokenAddress != address(0),
            'OPFCommunityFeeCollector: invalid token contract address'
        );

        require (
            IERC20Template(tokenAddress).transfer(
                collector,
                IERC20Template(tokenAddress).balanceOf(address(this))
            ),
            'OPFCommunityFeeCollector: failed to withdraw tokens'
        );
    }

    /**
     * @dev changeCollector
     *      change the current collector address. Only owner can do that.
     * @param newCollector the new collector address 
     */
    function changeCollector(
        address payable newCollector
    ) 
        external 
        onlyOwner 
    {
        require(
            newCollector != address(0),
            'OPFCommunityFeeCollector: invalid collector address'
        );
        collector = newCollector;
    }
}
