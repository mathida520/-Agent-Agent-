// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts/utils/cryptography/MessageHashUtils.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title HTLCMultiSig
 * @dev 结合了哈希时间锁定 (HTLC) 与 2-of-3 多重签名的智能合约。
 * 支持路径 A (正常交易) 和 路径 B (仲裁模式)。
 */
contract HTLCMultiSig is ReentrancyGuard {
    using ECDSA for bytes32;

    enum Status { Uninitialized, Locked, Completed, Refunded }

    struct Trade {
        address buyer;
        address seller;
        address arbiter;
        uint256 amount;
        bytes32 hashLock;
        uint256 timelock;
        Status status;
    }

    mapping(bytes32 => Trade) public trades;

    event Locked(bytes32 indexed tradeId, address buyer, address seller, uint256 amount, bytes32 hashLock, uint256 timelock);
    event Withdrawn(bytes32 indexed tradeId, address recipient, string method);
    event Refunded(bytes32 indexed tradeId, address recipient);

    /**
     * @dev 锁定资金并创建交易
     * @param _tradeId 交易唯一标识
     * @param _seller 卖家地址
     * @param _arbiter 仲裁方地址
     * @param _hashLock 原像的哈希值 (sha256)
     * @param _lockTime 锁定持续时间（秒）
     */
    function lock(
        bytes32 _tradeId,
        address _seller,
        address _arbiter,
        bytes32 _hashLock,
        uint256 _lockTime
    ) external payable {
        require(msg.value > 0, "Amount must be greater than 0");
        require(trades[_tradeId].status == Status.Uninitialized, "Trade ID already exists");
        require(_seller != address(0) && _arbiter != address(0), "Invalid addresses");

        trades[_tradeId] = Trade({
            buyer: msg.sender,
            seller: _seller,
            arbiter: _arbiter,
            amount: msg.value,
            hashLock: _hashLock,
            timelock: block.timestamp + _lockTime,
            status: Status.Locked
        });

        emit Locked(_tradeId, msg.sender, _seller, msg.value, _hashLock, trades[_tradeId].timelock);
    }

    /**
     * @dev 路径 A: 正常解锁。需要原像 + (买方和卖方的共同签名)
     * 注意：在实际应用中，如果买卖双方都同意，通常原像本身就足够证明交易完成。
     * 但根据要求，这里强制要求双重签名。
     */
    function withdrawWithPreimage(
        bytes32 _tradeId,
        bytes32 _preimage,
        bytes calldata _sig1,
        bytes calldata _sig2
    ) external nonReentrant {
        Trade storage trade = trades[_tradeId];
        require(trade.status == Status.Locked, "Invalid status");
        require(sha256(abi.encodePacked(_preimage)) == trade.hashLock, "Invalid preimage");

        bytes32 messageHash = MessageHashUtils.toEthSignedMessageHash(keccak256(abi.encodePacked(_tradeId, _preimage)));
        address signer1 = ECDSA.recover(messageHash, _sig1);
        address signer2 = ECDSA.recover(messageHash, _sig2);

        bool hasBuyer = (signer1 == trade.buyer || signer2 == trade.buyer);
        bool hasSeller = (signer1 == trade.seller || signer2 == trade.seller);

        require(hasBuyer && hasSeller, "Missing required signatures from buyer and seller");

        trade.status = Status.Completed;
        payable(trade.seller).transfer(trade.amount);

        emit Withdrawn(_tradeId, trade.seller, "Preimage + MultiSig");
    }

    /**
     * @dev 路径 B: 仲裁解锁。2-of-3 签名决定资金流向。
     * 允许的组合: (买方+仲裁方) 或 (卖方+仲裁方) 或 (买方+卖方)
     * @param _recipient 资金接收者
     */
    function resolveDispute(
        bytes32 _tradeId,
        address _recipient,
        bytes calldata _sig1,
        bytes calldata _sig2
    ) external nonReentrant {
        Trade storage trade = trades[_tradeId];
        require(trade.status == Status.Locked, "Invalid status");
        require(_recipient == trade.buyer || _recipient == trade.seller, "Invalid recipient");

        bytes32 messageHash = MessageHashUtils.toEthSignedMessageHash(keccak256(abi.encodePacked(_tradeId, _recipient)));
        address signer1 = ECDSA.recover(messageHash, _sig1);
        address signer2 = ECDSA.recover(messageHash, _sig2);

        uint256 validSignatures = 0;
        address[3] memory participants = [trade.buyer, trade.seller, trade.arbiter];
        
        address lastSigner = address(0);
        address[2] memory signers = [signer1, signer2];

        for(uint i=0; i<2; i++) {
            for(uint j=0; j<3; j++) {
                if(signers[i] == participants[j] && signers[i] != lastSigner) {
                    validSignatures++;
                    lastSigner = signers[i];
                    break;
                }
            }
        }

        require(validSignatures >= 2, "Need 2-of-3 signatures");

        trade.status = Status.Completed;
        payable(_recipient).transfer(trade.amount);

        emit Withdrawn(_tradeId, _recipient, "Arbitration");
    }

    /**
     * @dev 时间锁退款：超过规定时间无操作，买方撤回资金。
     */
    function refund(bytes32 _tradeId) external nonReentrant {
        Trade storage trade = trades[_tradeId];
        require(trade.status == Status.Locked, "Invalid status");
        require(block.timestamp >= trade.timelock, "Timelock not expired");

        trade.status = Status.Refunded;
        payable(trade.buyer).transfer(trade.amount);

        emit Refunded(_tradeId, trade.buyer);
    }
}
