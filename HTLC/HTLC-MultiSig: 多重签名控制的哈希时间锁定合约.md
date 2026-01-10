# HTLC-MultiSig: 多重签名控制的哈希时间锁定合约

## 项目概述

本项目提供了一个基于 Solidity 智能合约的 **多重签名控制的哈希时间锁定合约 (HTLC + Multi-Sig)** 解决方案。它将传统的 HTLC 机制与 2-of-3 多重签名逻辑相结合，旨在为去中心化交易提供更高的安全性和灵活性，特别适用于需要仲裁机制的跨链或链下交易场景。

该合约设计用于部署在 **Polygon** 或其他兼容 EVM 的网络上。

## 合约核心机制

合约的核心在于其灵活的资金解锁逻辑，它定义了三种可能的资金流向路径：正常交易路径（路径 A）、争议仲裁路径（路径 B）和时间锁退款路径。

### 1. 参与方

| 角色 | 描述 |
| :--- | :--- |
| **买方 (Buyer)** | 锁定资金的一方，在正常路径下提供原像。 |
| **卖方 (Seller)** | 资金的最终接收方，在正常路径下收款。 |
| **仲裁方 (Arbiter)** | 独立第三方，在发生争议时参与 2-of-3 签名以决定资金流向。 |

### 2. 解锁路径

| 路径 | 条件 | 结果 | 目的 |
| :--- | :--- | :--- | :--- |
| **路径 A (正常)** | 1. 买方提供正确的原像（Preimage）<br>2. 买方和卖方共同签名（2-of-2） | 资金转移给**卖方** | 正常完成交易，证明买方已满足哈希锁定的条件。 |
| **路径 B (仲裁)** | 2-of-3 签名（买方+仲裁方 或 卖方+仲裁方） | 资金转移给 2-of-3 签名指定的**接收方**（买方或卖方） | 解决交易争议，由多数参与方决定资金归属。 |
| **时间锁** | 超过预设的 `timelock` 时间，且交易未完成 | 资金退回给**买方** | 保护买方资金，防止资金被永久锁定。 |

## 合约结构 (`HTLCMultiSig.sol`)

合约使用了 OpenZeppelin 的 `ECDSA` 和 `ReentrancyGuard` 库来确保安全性和签名验证的正确性。

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts/utils/cryptography/MessageHashUtils.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

contract HTLCMultiSig is ReentrancyGuard {
    // ... 状态变量和结构体定义 ...

    // 1. lock: 买方锁定资金，设置哈希锁和时间锁
    function lock(bytes32 _tradeId, address _seller, address _arbiter, bytes32 _hashLock, uint256 _lockTime) external payable { ... }

    // 2. withdrawWithPreimage: 路径 A - 正常交易解锁
    function withdrawWithPreimage(bytes32 _tradeId, bytes32 _preimage, bytes calldata _sig1, bytes calldata _sig2) external nonReentrant { ... }

    // 3. resolveDispute: 路径 B - 仲裁解锁 (2-of-3 签名)
    function resolveDispute(bytes32 _tradeId, address _recipient, bytes calldata _sig1, bytes calldata _sig2) external nonReentrant { ... }

    // 4. refund: 时间锁到期退款
    function refund(bytes32 _tradeId) external nonReentrant { ... }
}
```

## 项目设置与部署

本项目使用 Hardhat 作为开发环境。

### 1. 环境准备

确保您已安装 Node.js (v18+) 和 pnpm。

```bash
# 切换到项目目录
cd htlc-multisig

# 安装依赖
pnpm install
```

### 2. 配置 `.env` 文件

在项目根目录创建 `.env` 文件，用于配置私钥和 RPC URL。

```
# 您的私钥，用于部署和交易
PRIVATE_KEY="YOUR_PRIVATE_KEY_HERE"

# Polygon 主网 RPC URL
POLYGON_RPC_URL="https://polygon-rpc.com"

# Polygon Mumbai 测试网 RPC URL
MUMBAI_RPC_URL="https://rpc-mumbai.maticvigil.com"

# PolygonScan API Key (用于合约验证)
POLYGONSCAN_API_KEY="YOUR_POLYGONSCAN_API_KEY"
```

### 3. 部署合约

使用 Hardhat 部署脚本将合约部署到 Polygon 网络（或 Mumbai 测试网）。

**部署到本地网络 (Hardhat Network):**

```bash
npx hardhat run scripts/deploy.js
```

**部署到 Mumbai 测试网:**

```bash
npx hardhat run scripts/deploy.js --network mumbai
```

**部署到 Polygon 主网:**

```bash
npx hardhat run scripts/deploy.js --network polygon
```

### 4. 运行测试

所有核心逻辑已通过测试文件 `test/HTLCMultiSig.test.js` 验证。

```bash
npx hardhat test
```

## 签名消息的构造

在 `withdrawWithPreimage` 和 `resolveDispute` 函数中，需要提供外部签名。签名消息的构造方式如下：

### 路径 A 签名消息

用于 `withdrawWithPreimage`，需要买方和卖方签名。

```
// 消息内容: keccak256(abi.encodePacked(tradeId, preimage))
// 签名方: 买方 (Buyer) 和 卖方 (Seller)
```

### 路径 B 签名消息

用于 `resolveDispute`，需要 2-of-3 签名。

```
// 消息内容: keccak256(abi.encodePacked(tradeId, recipientAddress))
// 签名方: 任意两方 (Buyer, Seller, Arbiter)
```

---
**作者**: Manus AI

**日期**: 2026年1月6日
