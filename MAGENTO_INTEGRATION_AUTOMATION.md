# Magento Integration 自动化设置指南

本指南介绍如何使用自动化脚本创建和配置 Magento Integration，完全绕过后台手动操作。

## 快速开始

### 1. 配置环境变量

```bash
# 复制示例配置文件
cp scripts/.env.example scripts/.env

# 编辑配置文件，填入实际值
nano scripts/.env
```

必需的环境变量：
- `MAGENTO_DB_HOST` - Magento 数据库主机
- `MAGENTO_DB_PORT` - Magento 数据库端口（默认 3306）
- `MAGENTO_DB_NAME` - Magento 数据库名称
- `MAGENTO_DB_USER` - 数据库用户名
- `MAGENTO_DB_PASSWORD` - 数据库密码
- `MAGENTO_BASE_URL` - Magento 商店 URL
- `INTEGRATION_NAME` - Integration 名称（默认：CJ_Sync）
- `INTEGRATION_EMAIL` - Integration 邮箱

### 2. 运行一键设置脚本

```bash
python scripts/setup_integration.py
```

脚本会自动执行：
1. 创建 Integration（如果不存在）
2. 激活 Integration
3. 生成 Access Token
4. 验证配置

### 3. 更新应用配置

脚本完成后，会输出 Access Token。将其添加到应用的 `.env` 文件：

```bash
MAGENTO_API_TOKEN=生成的Token
```

### 4. 重启应用

```bash
docker-compose restart app
```

## 脚本说明

### 核心脚本

| 脚本 | 功能 | 使用场景 |
|------|------|----------|
| `setup_integration.py` | 一键设置 | 首次设置或完整重置 |
| `create_integration_via_db.py` | 创建 Integration | 仅创建新 Integration |
| `activate_integration.py` | 激活 Integration | 激活已创建的 Integration |
| `generate_access_token.py` | 生成 Token | 生成或重新生成 Token |
| `verify_integration.py` | 验证配置 | 检查配置是否正确 |

### 使用场景

#### 场景 1: 首次设置
```bash
python scripts/setup_integration.py
```

#### 场景 2: 仅重新生成 Token
```bash
python scripts/setup_integration.py --skip-create --skip-activate
```

#### 场景 3: 验证现有配置
```bash
python scripts/setup_integration.py --verify-only
```

#### 场景 4: 激活已创建的 Integration
```bash
python scripts/setup_integration.py --skip-create --skip-token --skip-verify
```

## 工作原理

### 数据库操作流程

1. **创建 OAuth Consumer**
   - 在 `oauth_consumer` 表中创建记录
   - 生成 `consumer_key` 和 `consumer_secret`
   - 清空 `resource_id` 以确保使用角色权限

2. **创建 Integration**
   - 在 `integration` 表中创建记录
   - 关联 `consumer_id`

3. **创建 Authorization Role**
   - 在 `authorization_role` 表中创建角色
   - `role_type = 'U'`（用户类型）
   - `user_type = 'integration'`
   - `user_id = integration_id`

4. **创建 Authorization Rules**
   - 在 `authorization_rule` 表中创建权限规则
   - 为每个必需的资源创建 `allow` 规则

5. **激活 Integration**
   - 设置 `integration.status = 1`

6. **生成 Access Token**
   - 在 `oauth_token` 表中创建 Token 记录
   - 类型为 `access`
   - 设置过期时间

### 关键配置点

- **role_type**: 必须为 `'U'`（用户类型），不能是 `'G'`（组类型）
- **user_id**: 必须等于 `integration_id`，不能为 0
- **user_type**: 必须为 `'integration'`
- **resource_id**: 必须为 `NULL`，否则会覆盖角色权限

## 权限资源

脚本会自动配置以下权限：

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

### 问题 1: 数据库连接失败

**症状**: `❌ 数据库连接失败`

**解决方案**:
1. 检查数据库配置是否正确
2. 确认数据库服务正在运行
3. 确认数据库用户有足够权限
4. 检查防火墙设置

### 问题 2: Integration 已存在

**症状**: `✅ Integration 已存在`

**解决方案**:
- 这是正常情况，脚本会跳过创建
- 如需重新创建，先删除现有 Integration：
  ```sql
  DELETE FROM integration WHERE name = 'CJ_Sync';
  ```

### 问题 3: Token 生成失败

**症状**: `❌ 无法生成 Token`

**解决方案**:
1. 确认 Integration 已激活（`status = 1`）
2. 清除 Magento 缓存：
   ```bash
   php bin/magento cache:flush
   ```
3. 检查 `oauth_token` 表是否有写入权限

### 问题 4: API 权限验证失败

**症状**: `❌ Store Configs` 或 `❌ Products List`

**解决方案**:
1. 运行验证脚本查看详细错误：
   ```bash
   python scripts/verify_integration.py
   ```
2. 确认 `oauth_consumer.resource_id` 为 `NULL`：
   ```sql
   SELECT consumer_id, resource_id FROM oauth_consumer WHERE name = 'CJ_Sync';
   ```
3. 确认权限规则存在：
   ```sql
   SELECT * FROM authorization_rule WHERE role_id = (SELECT role_id FROM integration WHERE name = 'CJ_Sync');
   ```
4. 清除 Magento 缓存

### 问题 5: 401 Unauthorized 错误

**症状**: API 调用返回 401

**解决方案**:
1. 验证 Token 是否正确：
   ```bash
   python scripts/verify_integration.py
   ```
2. 检查 Token 是否过期
3. 确认 Integration 状态为激活
4. 清除 Magento 缓存
5. 重新生成 Token：
   ```bash
   python scripts/generate_access_token.py
   ```

## 安全注意事项

1. **数据库备份**: 在生产环境使用前，务必备份数据库
2. **权限控制**: 确保数据库用户只有必要的权限
3. **Token 安全**: 生成的 Token 应妥善保管，不要泄露
4. **环境变量**: 不要在代码中硬编码敏感信息
5. **访问控制**: 限制脚本文件的访问权限

## 维护

### 定期检查

建议定期运行验证脚本：

```bash
python scripts/verify_integration.py
```

### 更新 Token

如果 Token 过期或需要重新生成：

```bash
python scripts/generate_access_token.py
```

### 查看 Integration 状态

```sql
SELECT 
    i.integration_id,
    i.name,
    i.status,
    i.consumer_id,
    i.role_id,
    oc.name as consumer_name,
    ar.role_name
FROM integration i
LEFT JOIN oauth_consumer oc ON i.consumer_id = oc.consumer_id
LEFT JOIN authorization_role ar ON i.role_id = ar.role_id
WHERE i.name = 'CJ_Sync';
```

## 相关文档

- [scripts/README.md](scripts/README.md) - 详细脚本文档
- [FINAL_SOLUTION.md](FINAL_SOLUTION.md) - 问题诊断和解决方案

## 支持

如有问题，请：
1. 查看脚本输出的详细错误信息
2. 检查 Magento 日志文件
3. 运行验证脚本获取诊断信息


