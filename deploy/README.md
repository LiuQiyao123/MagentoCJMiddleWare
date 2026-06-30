# Magento-CJ 部署指南

## 架构

```
┌─────────────────────────────────┐    ┌──────────────────────────────────┐
│  沙箱环境（本地 WSL Docker）      │    │  正式环境（阿里云 ECS Docker）    │
│                                 │    │                                  │
│  shop-sandbox.yokileopard.top   │    │  shop.yokileopard.top            │
│  mcj-sandbox.yokileopard.top    │    │  mcj.yokileopard.top             │
│       ↑                         │    │       ↑                          │
│  Cloudflare Tunnel              │    │  Cloudflare Tunnel               │
│       ↑                         │    │       ↑                          │
│  localhost:8088 (Magento)       │    │  localhost:80 (Magento)          │
│  localhost:3000 (Middleware)    │    │  localhost:3000 (Middleware)     │
└─────────────────────────────────┘    └──────────────────────────────────┘
         ↑                                    ↑
         └──── 同一份镜像，同一份 Compose ──────┘
                      不同 .env
```

## 核心理念

**一套代码，两套环境，零差异部署。**

- `docker-compose.yml` 纳入 git 版本管理，沙箱和正式完全一致
- 不同的 `.env` 文件切换环境
- 沙箱测通什么，正式就是什么

## 快速开始

### 沙箱（本地 WSL）

```bash
# 1. 部署中间件
cd /home/yao/MagentoCJMiddleWare
./deploy/deploy.sh sandbox up

# 2. 部署 Magento（如需要）
cd /home/yao/magento-project
cp ../MagentoCJMiddleWare/deploy/magento/.env.sandbox .env
docker compose up -d
```

### 正式（阿里云 ECS）

```bash
# 1. 克隆代码
git clone git@github.com:LiuQiyao123/MagentoCJMiddleWare.git /opt/magento-cj

# 2. 创建生产环境配置
cp /opt/magento-cj/deploy/env/production.env /opt/magento-cj/.env
# 编辑 .env 修改密码和密钥

# 3. 部署
cd /opt/magento-cj
./deploy/deploy.sh production up
```

### Magento 数据库迁移

从沙箱到正式的数据迁移：

```bash
# 在本地 dump
docker exec magento-project-db-1 mysqldump -u magento -pmagento magento > magento_dump.sql

# 传到 ECS 导入
scp magento_dump.sql ecs-user@<ECS_IP>:/tmp/
docker exec -i ecs-db-container mysql -u magento -pmagento magento < /tmp/magento_dump.sql
```

## 常用命令

```bash
# 部署
./deploy/deploy.sh sandbox up          # 启动沙箱
./deploy/deploy.sh production up        # 启动正式
./deploy/deploy.sh sandbox down         # 停止沙箱
./deploy/deploy.sh sandbox restart      # 重启沙箱

# 查看状态
./deploy/deploy.sh sandbox status
./deploy/deploy.sh sandbox logs

# 重建
./deploy/deploy.sh sandbox rebuild      # 重新构建镜像
```

## 环境差异清单

| 维度 | 沙箱（WSL） | 正式（ECS） |
|------|-----------|-----------|
| Magento 端口 | 8088 | 80 |
| MySQL 端口 | 33061 (host) | 3306 (internal) |
| Magento URL | localhost:8088 | shop.yokileopard.top |
| 中间件 URL | localhost:3000 | mcj.yokileopard.top |
| DEBUG | true | false |
| CJ 模式 | 开发模式 | 正式模式 |
| CORS | localhost + tunnel | 仅正式域名 |
| 日志级别 | DEBUG | INFO |
