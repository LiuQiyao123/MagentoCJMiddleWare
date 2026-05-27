# Changelog — Magento-CJ Middleware

> 更新时间：2026-05-27

---

## 👤 用户视角

### 新增功能

- **商品同步**：粘贴 CJ Dropshipping 商品链接，自动同步到 Magento
- **实时进度**：同步过程中实时显示进度条、步骤日志、错误记录
- **一键回滚**：同步失败后可一键删除本次创建的所有商品
- **任务列表**：查看历史同步任务的状态和详情
- **Web 界面**：访问 `https://mcj.yokileopard.top` 即可操作

### 数据同步内容

| 字段 | 来源 | 说明 |
|------|------|------|
| 商品名 | CJ `productNameEn` | 完整的英文商品标题 |
| 售价 | CJ `suggestSellPrice` | CJ 建议零售价 |
| 进货价 | CJ `sellPrice` | 存储在 `cost_price` 属性 |
| 海关编码 | CJ `entryCode` | HS Code |
| 申报品名 | CJ `entryNameEn` | 海关申报名称 |
| 商品图片 | CJ `bigImage` | 自动下载并上传到 Magento |
| 变体图片 | CJ variant `variantImage` | 每个变体对应独立图片 |
| 变体（独立商品） | CJ variants | 每个颜色/尺寸创建独立子商品 |

### 已知问题

- 变体之间没有可配置商品关联（正在开发中）
- 定价需要手动调整（后续开发 AI 定价模块）
- 图片下载较慢（后续改为并发下载）

---

## 📊 产品经理视角

### 已上线功能（MVP）

| 功能 | 状态 | 说明 |
|------|------|------|
| CJ 商品 → Magento 同步 | ✅ | 手动输入URL，一键同步 |
| 商品基本信息 | ✅ | 名称/售价/进价/重量/描述 |
| 海关信息 | ✅ | HS code + 申报品名 |
| 商品图片 | ✅ | 主图 + 变体图 |
| 多变体支持 | ✅ | 独立子商品 |
| 异步任务 | ✅ | 后台执行，不阻塞 |
| 错误处理 | ✅ | 自动重试 + 日志记录 |
| 数据回滚 | ✅ | 一键删除 |
| Token 自动刷新 | ✅ | 过期自动处理 |

### 开发中

| 功能 | 进度 | 说明 |
|------|------|------|
| 可配置商品关联 | ⏳ WIP | 颜色/尺寸属性已创建，API 400 排错中 |
| 变体独立定价 | 📋 Planned | 每个变体使用 CJ variantSellPrice |
| 变体独立库存 | 📋 Planned | 同步 CJ inventoryNum |

### 后续规划

- AI 定价模块（TikTok 同款价格爬取 + 分析报告）
- 物流成本核算（CJ 物流方案综合评估）
- 批量同步（一次同步多个商品）
- 自动同步（定时任务后台同步）
- 库存自动同步

---

## 🔧 开发视角

### 架构

```
用户 → mcj.yokileopard.top
         ↓
    FastAPI (port 3000)
         ├─ web 前端 (Jinja2)
         ├─ REST API (FastAPI Router)
         ├─ Celery 任务队列 (Redis)
         └─ SQLAlchemy + MySQL
              ↓
         Magento REST API (https://shop.yokileopard.top)
              ↓
         Magento MySQL (magento-project-db-1)
```

### 核心文件

| 文件 | 功能 |
|------|------|
| `app/main.py` | FastAPI 应用入口，生命周期管理 |
| `app/api/v1/products.py` | 产品同步 API + 异步任务 `_run_sync` |
| `app/services/product_sync.py` | 产品同步逻辑（build/upload/parse） |
| `app/services/task_manager.py` | 异步任务状态管理（Redis） |
| `app/services/attribute_mapper.py` | CJ 维度 → Magento 属性映射 |
| `app/clients/cj_client.py` | CJ Dropshipping API 客户端 |
| `app/clients/magento_client.py` | Magento REST API 客户端（带自动token刷新） |
| `app/templates/index.html` | 前端页面（异步进度 + 任务列表 + 回滚） |
| `app/config/settings.py` | pydantic 配置管理（.env） |
| `app/services/celery_app.py` | Celery 配置（未使用，待接入） |
| `docker-compose.yml` | MySQL + Redis + App 容器编排 |

### 关键实现

#### 异步任务系统
- `POST /api/v1/products/sync/single` 立即返回 `task_id`
- `asyncio.create_task` 后台执行同步
- Redis hash 存储任务状态（`async_task:{id}`）
- 前端轮询 `GET /sync/status/{id}` 更新 UI

#### Token 自动刷新
- MagentoClient._make_request 中捕获 401
- 调用 `POST /integration/admin/token` 重新登录
- 更新 `self.api_token` 后重试

#### 图片上传
- httpx 下载 CJ CDN 图片
- base64 编码
- POST `Magento /products/{sku}/media`

#### 属性映射
- 关键词匹配（color/colour/颜色 → cj_color）
- 编辑距离模糊匹配 ≤2（coloer → color）
- pymysql 直连 Magento DB 创建属性选项

### 部署

```bash
# 启动服务
cd ~/MagentoCJMiddleWare && docker compose up -d

# 更新代码
docker cp app/services/*.py magento_cj_app:/app/app/services/
docker cp app/api/v1/*.py magento_cj_app:/app/app/api/v1/
docker cp app/templates/*.html magento_cj_app:/app/app/templates/
docker restart magento_cj_app

# 查看日志
docker logs magento_cj_app -f
```

### Git

```
分支: feature/async-core-v2
远端: origin/feature/async-core-v2
备份: feature/sync-before-images
```
