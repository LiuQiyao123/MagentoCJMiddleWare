# 中间件配置指南

## 安全配置步骤

### 1. 创建环境变量文件

**重要：** 永远不要将 `.env` 文件提交到GitHub！

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑配置文件，填入真实的API密钥
nano .env
```

### 2. 必需的环境变量

#### Magento配置
```bash
# Magento基础URL（您的Cloudflare域名）
MAGENTO_BASE_URL=https://your-magento-domain.com

# Magento API Token（需要您在Magento后台生成）
MAGENTO_API_TOKEN=your_generated_token_here

# Magento管理员账户（用于API认证）
MAGENTO_API_USER=admin
MAGENTO_API_PASSWORD=your_admin_password
```

#### CJ Dropshipping配置
```bash
# CJ API基础URL（通常不需要修改）
CJ_API_BASE_URL=https://developers.cjdropshipping.com/api2.0/v1

# CJ账户信息（需要您在CJ后台获取）
CJ_API_EMAIL=your_cj_email@example.com
CJ_API_PASSWORD=your_cj_api_key  # 这就是您的API Key
```

#### 数据库配置
```bash
# MySQL数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_NAME=magento_cj_middleware
DB_USER=root
DB_PASSWORD=your_database_password
```

#### 安全配置
```bash
# 应用密钥（用于JWT等安全功能）
SECRET_KEY=your_secret_key_here
JWT_SECRET=your_jwt_secret_here
```

### 3. 验证配置

```bash
# 测试配置是否正确
python -c "from app.config.settings import get_settings; print('配置加载成功')"
```

## 部署检查清单

- [ ] `.env` 文件已创建并包含所有必需变量
- [ ] `.env` 文件已添加到 `.gitignore`
- [ ] 所有API密钥都是有效的
- [ ] 数据库连接正常
- [ ] Magento API可以正常访问
- [ ] CJ API可以正常访问

## 安全建议

1. **定期轮换密钥**：建议每3-6个月更换一次API密钥
2. **最小权限原则**：只给中间件必要的API权限
3. **监控访问日志**：定期检查API调用日志
4. **备份配置**：安全备份您的 `.env` 文件 