# HTLCMultiSig 合约部署与交互指南 (Polygon 测试网)

本文档提供了在 Polygon Mumbai 测试网上部署和交互 `HTLCMultiSig` 智能合约的详细步骤，并演示了两种核心解锁路径：正常交易（路径 A）和仲裁解决（路径 B）。

---

## 1. 环境准备与项目配置

### 1.1. 前提条件

您需要准备以下环境和信息：

1.  **Node.js** (v18+) 和 **pnpm**。
2.  **Hardhat** 开发环境（已在工程中配置）。
3.  **Polygon Mumbai 测试网** 的 RPC URL [1]。
4.  一个用于部署和交易的 **私钥**。
5.  用于测试的 **测试网 MATIC**（可从水龙头获取 [2]）。

### 1.2. 配置 `.env` 文件

在项目根目录创建 `.env` 文件，并填入您的配置信息。

```dotenv
# 部署账户的私钥。请注意安全，不要在生产环境中使用此私钥。
PRIVATE_KEY="YOUR_DEPLOYER_PRIVATE_KEY"

# Polygon Mumbai 测试网 RPC URL
MUMBAI_RPC_URL="https://rpc-mumbai.maticvigil.com"

# PolygonScan API Key (可选，用于验证合约)
POLYGONSCAN_API_KEY="YOUR_POLYGONSCAN_API_KEY"
```

### 1.3. 安装依赖

进入项目目录并安装所有依赖：

```bash
cd htlc-multisig
pnpm install
```

## 2. 合约部署

使用 Hardhat 部署脚本将合约部署到 Mumbai 测试网。

```bash
npx hardhat run scripts/deploy.js --network mumbai
```

**预期输出:**

```
Deploying HTLCMultiSig...
HTLCMultiSig deployed to: 0x... (您的合约地址)
```

请记录下部署的合约地址，后续交互将使用此地址。

## 3. 交互流程演示

我们将模拟一个交易场景，其中包含买方 (Buyer)、卖方 (Seller) 和仲裁方 (Arbiter)。

### 3.1. 模拟账户准备

在实际操作中，您需要准备三个独立的私钥来模拟这三个角色。在 Hardhat 环境中，我们可以使用 Hardhat 提供的测试账户。

| 角色 | 作用 |
| :--- | :--- |
| **Buyer** | 锁定资金，发起交易。 |
| **Seller** | 接收资金，完成交易。 |
| **Arbiter** | 仲裁方，参与路径 B 的签名。 |

### 3.2. 路径 A：正常解锁流程 (Preimage + 双签)

**目标:** 卖方成功提取资金。

#### 步骤 1: 锁定资金 (`lock`)

买方将资金锁定在合约中，并设置哈希锁和时间锁。

*   **交易 ID (`tradeId`)**: 唯一标识符，例如 `0x...`
*   **原像哈希 (`hashLock`)**: 预先计算的哈希值。
*   **时间锁 (`timelock`)**: 资金的最早退款时间。

#### 步骤 2: 签名消息构造

卖方需要买方提供的原像 (`preimage`) 来计算哈希，并需要买方和卖方对特定消息进行签名。

**签名消息内容:**

> `keccak256(abi.encodePacked(tradeId, preimage))`

买方和卖方分别使用自己的私钥对该消息进行签名，生成 `sigBuyer` 和 `sigSeller`。

#### 步骤 3: 提取资金 (`withdrawWithPreimage`)

卖方调用 `withdrawWithPreimage` 函数，传入：
1.  `tradeId`
2.  `preimage`
3.  `sigBuyer`
4.  `sigSeller`

合约验证：
1.  `sha256(preimage)` 是否等于 `hashLock`。
2.  `sigBuyer` 和 `sigSeller` 是否有效且来自正确的买方和卖方地址。

验证通过后，资金将转移给卖方。

### 3.3. 路径 B：仲裁解锁流程 (2-of-3 签名)

**目标:** 仲裁方介入，决定资金退回给买方。

#### 步骤 1: 锁定资金 (与路径 A 相同)

买方锁定资金，但交易因故无法通过路径 A 完成。

#### 步骤 2: 仲裁签名消息构造

仲裁方和另一方（例如买方）对仲裁结果进行签名。

**签名消息内容:**

> `keccak256(abi.encodePacked(tradeId, recipientAddress))`

其中 `recipientAddress` 是仲裁决定的资金接收方（买方或卖方）。

假设仲裁决定退款给买方，则：
*   **签名方:** 买方 (Buyer) 和 仲裁方 (Arbiter)。
*   **消息:** `keccak256(abi.encodePacked(tradeId, BuyerAddress))`

买方和仲裁方分别签名，生成 `sigBuyer` 和 `sigArbiter`。

#### 步骤 3: 执行仲裁 (`resolveDispute`)

任意一方调用 `resolveDispute` 函数，传入：
1.  `tradeId`
2.  `recipientAddress` (买方地址)
3.  `sig1` (`sigBuyer`)
4.  `sig2` (`sigArbiter`)

合约验证：
1.  `sig1` 和 `sig2` 恢复出的地址是否是 (Buyer, Seller, Arbiter) 三者中的任意两个。
2.  验证通过后，资金将转移给 `recipientAddress`。

### 3.4. 脚本演示

您可以使用项目中的 `scripts/interact.js` 脚本在本地 Hardhat 网络上完整运行上述两个流程，以验证逻辑和查看输出。

```bash
npx hardhat run scripts/interact.js
```

**预期输出将清晰展示资金锁定、签名生成和最终提取/仲裁的每一步余额变化。**

---

## 4. 附加路径：时间锁退款

如果交易长时间未完成，且时间锁到期，买方可以调用 `refund` 函数取回资金。

#### 步骤 1: 等待时间锁到期

等待 `timelock` 字段中记录的区块时间戳过去。

#### 步骤 2: 退款 (`refund`)

买方调用 `refund` 函数，传入 `tradeId`。

合约验证：
1.  交易状态是否为 `Locked`。
2.  当前区块时间戳是否大于 `timelock`。

验证通过后，资金将退回给买方。

---

## 5. 引用

[1] Polygon Mumbai Testnet RPC Endpoints. *Polygon Documentation*.
[2] Polygon Faucet. *Matic Faucet*.
