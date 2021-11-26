// SPDX-License-Identifier: MIT
pragma solidity ^0.5.7;

import "OpenZeppelin/openzeppelin-contracts@2.1.1/contracts/token/ERC20/SafeERC20.sol";
import "OpenZeppelin/openzeppelin-contracts@2.1.1/contracts/utils/Address.sol";
import "OpenZeppelin/openzeppelin-contracts@2.1.1/contracts/math/SafeMath.sol";

/**
 * @title VestingWallet057
 * @dev This contract handles the vesting of Eth and ERC20 tokens for a given beneficiary. Custody of multiple tokens
 * can be given to this contract, which will release the token to the beneficiary following a given vesting schedule.
 * The vesting schedule is customizable through the {vestedAmount} function.
 *
 * Any token transferred to this contract will follow the vesting schedule as if they were locked from the beginning.
 * Consequently, if the vesting has already started, any amount of tokens sent to this contract will (at least partly)
 * be immediately releasable.
 */
contract VestingWallet057 {
    event EtherReleased(uint256 amount);
    event ERC20Released(address token, uint256 amount);

    uint256 private _released;
    mapping(address => uint256) private _erc20Released;
    //address private immutable _beneficiary; //>=0.6.5. Makes them read-only
    address private _beneficiary;
    //uint64 private immutable _start; //>=0.6.5
    uint64 private _start;
    //uint64 private immutable _duration; //>=0.6.5
    uint64 private _duration;

    /**
     * @dev Set the beneficiary, start timestamp and vesting duration of the vesting wallet.
     */
    constructor(
        address beneficiaryAddress,
        uint64 startTimestamp,
        uint64 durationSeconds
    ) public {
        require(beneficiaryAddress != address(0), "VestingWallet057: beneficiary is zero address");
        _beneficiary = beneficiaryAddress;
        _start = startTimestamp;
        _duration = durationSeconds;
    }

    /**
     * @dev The contract should be able to receive Eth.
     */
    function () external payable {}

    /**
     * @dev Getter for the beneficiary address.
     */
    function beneficiary() public view returns (address) {
        return _beneficiary;
    }

    /**
     * @dev Getter for the start timestamp.
     */
    function start() public view returns (uint256) {
        return _start;
    }

    /**
     * @dev Getter for the vesting duration.
     */
    function duration() public view returns (uint256) {
        return _duration;
    }

    /**
     * @dev Amount of eth already released
     */
    function released() public view returns (uint256) {
        return _released;
    }

    /**
     * @dev Amount of token already released
     */
    function released(address token) public view returns (uint256) {
        return _erc20Released[token];
    }

    /**
     * @dev Release the native token (ether) that have already vested.
     *
     * Emits a {TokensReleased} event.
     */
    function release() public {
        uint256 releasable = vestedAmount(uint64(block.timestamp)) - released();
        _released += releasable;
        emit EtherReleased(releasable);
	address payable b = address(uint160(beneficiary()));
	b.send(releasable);
    }

    /**
     * @dev Release the tokens that have already vested.
     *
     * Emits a {TokensReleased} event.
     */
    function release(address token) public {
        uint256 releasable = vestedAmount(token, uint64(block.timestamp)) - released(token);
        _erc20Released[token] += releasable;
        emit ERC20Released(token, releasable);
        SafeERC20.safeTransfer(IERC20(token), beneficiary(), releasable);
    }

    /**
     * @dev Calculates the amount of ether that has already vested. Default implementation is a linear vesting curve.
     */
    function vestedAmount(uint64 timestamp) public view returns (uint256) {
        return _vestingSchedule(address(this).balance + released(), timestamp);
    }

    /**
     * @dev Calculates the amount of tokens that has already vested. Default implementation is a linear vesting curve.
     */
    function vestedAmount(address token, uint64 timestamp) public view returns (uint256) {
        return _vestingSchedule(IERC20(token).balanceOf(address(this)) + released(token), timestamp);
    }

    /**
     * @dev implementation of the vesting formula. This returns the amout vested, as a function of time, for
     * an asset given its total historical allocation.
     */
    function _vestingSchedule(uint256 totalAllocation, uint64 timestamp) internal view returns (uint256) {
        if (timestamp < start()) {
            return 0;
        } else if (timestamp > start() + duration()) {
            return totalAllocation;
        } else {
            return (totalAllocation * (timestamp - start())) / duration();
        }
    }
}
