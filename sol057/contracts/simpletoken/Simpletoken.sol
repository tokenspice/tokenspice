pragma solidity ^0.5.7;
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)

import "OpenZeppelin/openzeppelin-contracts@2.1.1/contracts/math/SafeMath.sol";

contract Simpletoken {

    using SafeMath for uint256;

    string public symbol;
    string public  name;
    uint256 public decimals;
    uint256 public totalSupply;

    mapping(address => uint256) balances;
    mapping(address => mapping(address => uint256)) allowed;


    event Transfer(address from, address to, uint256 value);
    event Approval(address owner, address spender, uint256 value);

    constructor(
        string memory _symbol,
        string memory _name,
        uint256 _decimals,
        uint256 _totalSupply
    )
        public
    {
        symbol = _symbol;
        name = _name;
        decimals = _decimals;
        totalSupply = _totalSupply;
        balances[msg.sender] = _totalSupply;
        emit Transfer(address(0), msg.sender, _totalSupply);
    }

    //fallback () external payable { // >= 0.6.0
    function () external payable { //0.5.x
        revert();
    }

    function balanceOf(address _owner) public view returns (uint256) {
        return balances[_owner];
    }

    function allowance(
        address _owner,
        address _spender
    )
        public
        view
        returns (uint256)
    {
        return allowed[_owner][_spender];
    }

    function approve(address _spender, uint256 _value) public returns (bool) {
        allowed[msg.sender][_spender] = _value;
        emit Approval(msg.sender, _spender, _value);
        return true;
    }

    function transfer(address _to, uint256 _value) public returns (bool) {
        balances[msg.sender] = balances[msg.sender].sub(_value);
        balances[_to] = balances[_to].add(_value);
        emit Transfer(msg.sender, _to, _value);
        return true;
    }

    function transferFrom(
        address _from,
        address _to,
        uint256 _value
    )
        public
        returns (bool)
    {
        require(allowed[_from][msg.sender] >=_value, "Insufficient allowance");
        balances[_from] = balances[_from].sub(_value);
        allowed[_from][msg.sender] = allowed[_from][msg.sender].sub(_value);
        balances[_to] = balances[_to].add(_value);
        emit Transfer(_from, _to, _value);
        return true;
    }

}
