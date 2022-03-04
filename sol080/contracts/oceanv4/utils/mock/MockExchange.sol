pragma solidity 0.8.10;
// Copyright BigchainDB GmbH and Ocean Protocol contributors
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
// Code is Apache-2.0 and docs are CC-BY-4.0

import "../../interfaces/IERC20Template.sol";


contract MockExchange {



    function depositWithPermit(
        address _token,
        uint256 _amount,
        uint256 _deadline,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external {
        IERC20Template(_token).permit(
            msg.sender,
            address(this),
            _amount,
            _deadline,
            v,
            r,
            s
        );
        IERC20Template(_token).transferFrom(msg.sender, address(this), _amount);
    }

    function deposit(address _token, uint256 _amount) external {
        IERC20Template(_token).transferFrom(msg.sender, address(this), _amount);
    }
}
