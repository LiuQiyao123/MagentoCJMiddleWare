# Magento Integration 自动化脚本

本目录包含用于自动化创建、激活和配置 Magento Integration 的脚本集合。

## 脚本列表

### 1. `create_integration_via_db.py`
通过直接操作 Magento 数据库创建 Integration。

**功能：**
- 创建 OAuth Consumer
- 创建 Authorization Role
- 创建 Authorization Rules（权限规则）
- 创建 Integration 记录
- 清空 `oauth_consumer.resource_id` 以确保权限生效

**使用方法：**
```bash
python scripts/create_integration_via_db.py
```

### 2. `activate_integration.py`
在数据库中激活 Integration（设置 `status = 1`）。

**使用方法：**
```bash
python scripts/activate_integration.py
```

### 3. `generate_access_token.py`
生成并获取 Integration 的 Access Token。

**使用方法：**
```bash
python scripts/generate_access_token.py
```

### 4. `verify_integration.py`
验证 Integration 配置和 API 权限。

**功能：**
- 验证数据库配置（Integration、Consumer、Role、Permissions）
- 验证 API 访问权限（基础连接、Store Configs、Products List、Create Product）

**使用方法：**
```bash
python scripts/verify_integration.py
```

### 5. `setup_integration.py` ⭐
**一键设置脚本**，整合所有步骤。

**使用方法：**
```bash
# 完整设置流程
python scripts/setup_integration.py

# 跳过创建，只激活和生成 Token
python scripts/setup_integration.py --skip-create

# 只验证现有配置
python scripts/setup_integration.py --verify-only
```

**选项：**
- `--skip-create`: 跳过创建 Integration
- `--skip-activate`: 跳过激活 Integration
- `--skip-token`: 跳过生成 Token
- `--skip-verify`: 跳过验证步骤
- `--verify-only`: 只运行验证步骤

## 环境变量配置

创建 `.env` 文件（参考 `scripts/.env.example`）：

```bash
# Magento 数据库配置
MAGENTO_DB_HOST=localhost
MAGENTO_DB_PORT=3306
MAGENTO_DB_NAME=magento
MAGENTO_DB_USER=root
MAGENTO_DB_PASSWORD=your_password

# Magento API 配置
MAGENTO_BASE_URL=https://shop.yokileopard.top
MAGENTO_API_TOKEN=your_access_token_here

# Integration 配置
INTEGRATION_NAME=CJ_Sync
INTEGRATION_EMAIL=cj_sync@example.com
```

## 完整流程

### 方法 1: 使用一键设置脚本（推荐）

```bash
# 1. 配置环境变量
cp scripts/.env.example scripts/.env
# 编辑 scripts/.env 填入实际值

# 2. 运行一键设置
python scripts/setup_integration.py

# 3. 更新应用 .env 文件中的 MAGENTO_API_TOKEN
# 4. 重启应用程序
```

### 方法 2: 手动执行各步骤

```bash
# 1. 创建 Integration
python scripts/create_integration_via_db.py

# 2. 激活 Integration
python scripts/activate_integration.py

# 3. 生成 Access Token
python scripts/generate_access_token.py

# 4. 验证配置
python scripts/verify_integration.py

# 5. 更新应用 .env 文件中的 MAGENTO_API_TOKEN
# 6. 重启应用程序
```

## 权限资源列表

脚本会自动创建以下权限资源：

- `Magento_Catalog::products` - 产品管理
- `Magento_Catalog::categories` - 分类管理
- `Magento_Backend::store` - 商店配置
- `Magento_Backend::config` - 系统配置
- `Magento_InventoryApi::inventory` - 库存 API
- `Magento_Sales::sales` - 销售管理
- `Magento_Sales::sales_operation` - 销售操作
- `Magento_Customer::customer` - 客户管理
- `Magento_Customer::group` - 客户组管理
- `Magento_Sales::shipment` - 发货管理
- `Magento_Sales::shipment_capture` - 发货捕获
- `Magento_Sales::shipment_track` - 发货跟踪
- `Magento_Sales::shipment_view` - 发货查看

## 故障排除

### 1. 数据库连接失败
- 检查 `MAGENTO_DB_HOST`、`MAGENTO_DB_PORT`、`MAGENTO_DB_USER`、`MAGENTO_DB_PASSWORD` 是否正确
- 确认数据库服务正在运行
- 确认数据库用户有足够的权限

### 2. Integration 创建失败
- 检查 Integration 名称是否已存在
- 确认数据库表结构正确
- 查看脚本输出的详细错误信息

### 3. Token 生成失败
- 确认 Integration 已激活（`status = 1`）
- 检查 Magento 缓存是否已清除
- 确认 Magento API 端点可访问

### 4. API 权限验证失败
- 运行 `verify_integration.py` 查看详细验证结果
- 确认 `oauth_consumer.resource_id` 已清空
- 确认 `authorization_rule` 表中存在相应的权限规则
- 清除 Magento 缓存：`php bin/magento cache:flush`

## 注意事项

1. **数据库操作风险**：这些脚本直接操作 Magento 数据库，请在生产环境使用前备份数据库。

2. **权限要求**：脚本需要数据库的写权限，确保数据库用户有足够的权限。

3. **Magento 缓存**：创建或修改 Integration 后，需要清除 Magento 缓存：
   ```bash
   php bin/magento cache:flush
   ```

4. **Token 安全**：生成的 Access Token 应妥善保管，不要泄露。

5. **脚本幂等性**：脚本支持重复运行，会检查现有记录避免重复创建。

## 技术细节

### 数据库表结构

脚本操作以下 Magento 数据库表：

- `oauth_consumer` - OAuth 消费者
- `authorization_role` - 授权角色
- `authorization_rule` - 授权规则
- `integration` - Integration 记录
- `oauth_token` - OAuth Token

### 关键配置

- `role_type = 'U'` - 用户类型（Integration 必须使用 'U'）
- `user_type = 'integration'` - 用户类型标识
- `user_id = integration_id` - 关联到 Integration ID
- `resource_id = NULL` - 清空以使用角色权限

## 支持

如有问题，请检查：
1. 脚本输出的错误信息
2. Magento 日志文件
3. 数据库连接和权限


