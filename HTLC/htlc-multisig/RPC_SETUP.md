# 如何获取可靠的 Mumbai 测试网 RPC URL

公共 RPC 端点经常不稳定，建议使用以下服务获取免费的 RPC URL：

## 方法 1: 使用 Alchemy (推荐)

### 步骤：
1. 访问 [Alchemy](https://www.alchemy.com/) 并注册免费账号
2. 登录后，点击 **"Create App"** 或 **"Create New App"**
3. 选择：
   - **Chain**: Polygon
   - **Network**: Mumbai (Testnet)
4. 创建后，点击你的 App，找到 **"HTTP"** 或 **"RPC URL"**
5. 复制 URL，格式类似：`https://polygon-mumbai.g.alchemy.com/v2/YOUR_API_KEY`

### 更新 .env 文件：
```env
MUMBAI_RPC_URL="https://polygon-mumbai.g.alchemy.com/v2/YOUR_API_KEY"
```

## 方法 2: 使用 Infura

### 步骤：
1. 访问 [Infura](https://infura.io/) 并注册免费账号
2. 登录后，创建新项目
3. 选择 **Polygon PoS** 网络
4. 在项目设置中找到 **Mumbai Testnet** 的端点
5. 复制 URL，格式类似：`https://polygon-mumbai.infura.io/v3/YOUR_PROJECT_ID`

### 更新 .env 文件：
```env
MUMBAI_RPC_URL="https://polygon-mumbai.infura.io/v3/YOUR_PROJECT_ID"
```

## 方法 3: 使用 QuickNode

1. 访问 [QuickNode](https://www.quicknode.com/)
2. 注册并创建 Mumbai 测试网端点
3. 复制提供的 RPC URL

## 方法 4: 使用公共端点（不推荐，可能不稳定）

如果只是临时测试，可以尝试：
- `https://rpc-mumbai.maticvigil.com` (可能不稳定)
- `https://matic-mumbai.chainstacklabs.com` (可能不稳定)

## 更新 .env 文件后

更新 `.env` 文件中的 `MUMBAI_RPC_URL` 后，重新运行部署命令：

```bash
./node_modules/.bin/hardhat --config hardhat.config.js run scripts/deploy.js --network mumbai
```

## 为什么需要自己的 RPC URL？

1. **稳定性**: 公共端点经常超时或限制访问
2. **速率限制**: 免费服务通常有更高的速率限制
3. **可靠性**: 自己的端点更稳定，适合开发和测试

## 快速开始

**推荐使用 Alchemy**，因为：
- 免费注册
- 提供 300M 计算单元/月（足够测试使用）
- 界面友好，设置简单
- 稳定可靠

注册后，将 RPC URL 更新到 `.env` 文件即可开始部署！

