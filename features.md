## 系统功能一览

- 定位: Magento 2 与 CJ Dropshipping 的中台集成，打通商品、订单、库存、物流全链路
- 能力: 异步任务、Redis 队列、计划任务、速率限制、自动重试、指标与健康检查

### 对外 API（v1）

- 商品
  - POST `/api/v1/products/sync/single`: 通过 CJ 商品链接同步单商品到 Magento（含数据缓存、失败容错）
  - POST `/api/v1/products/sync/inventory`: 从 CJ 同步库存到 Magento（支持指定 product_ids）
  - GET `/api/v1/products/sync/status`: 获取同步任务状态（当前为占位返回）
- 订单
  - POST `/api/v1/orders/sync/to-cj`: 将 Magento 新订单异步同步到 CJ（后台任务触发）
  - GET `/api/v1/orders/tracking/{order_id}`: 查询 CJ 订单详情与物流跟踪
- 分类
  - GET `/api/v1/categories/`: 透传 Magento 分类树
- 监控/诊断
  - GET `/api/v1/monitor/rate-limiter/status`: CJ API 速率限制器状态
  - GET `/api/v1/monitor/token/status`: CJ Token 状态（有效期、预览）
  - POST `/api/v1/monitor/token/refresh`: 强制刷新 CJ Token
  - GET `/api/v1/monitor/system/status`: 汇总系统健康度与预警
- Webhooks
  - POST `/api/v1/webhooks/magento/order`: 接收 Magento 新订单 Webhook，写入 Redis Stream

### 健康检查与指标

- GET `/health`、`/health/detailed`、`/health/ready`、`/health/live`
- GET `/health/queue-stats`、`/health/scheduler-stats`
- GET `/metrics`: Prometheus 指标
- GET `/`: 简单静态首页

## 同步与后台任务

- 订单同步
  - 拉取近 N 小时 Magento 订单，去重后创建 CJ 订单并记录映射
  - 状态回流：批量查询 CJ 状态，更新本地与 Magento，回写物流跟踪号
  - 取消：按映射取消 CJ 订单并同步 Magento
- 商品同步
  - 从 CJ 按分类/关键字分页拉取商品，转 Magento 数据结构后创建/更新
  - 库存：依据映射拉取 CJ 库存并更新 Magento Stock
  - 变体与图片：变体最小化处理；图片上传暂跳过以规避 Magento 校验错误
- 计划任务（Scheduler）
  - 每小时订单同步、每日商品同步、每日清理、每 5 分钟健康检查（均入队执行）
- 队列与工作进程
  - Redis List 队列：`product_sync`、`order_sync`、`maintenance`（入队/出队/统计/清空）
  - Redis Stream：消费订单 Webhook 事件，调用供应商网关下单并落库映射

## 第三方集成

- CJ Dropshipping
  - 认证与 Token 缓存/刷新（5 分钟限频、15 天有效期、自动回退）
  - 商品：搜索、详情、变体、库存
  - 订单：创建、查询、取消
  - 物流：方式、运费、轨迹查询
  - 参考数据：分类、国家、地址校验
- Magento
  - 产品：查询、创建/更新、删除、属性/属性集
  - 库存：SKU 维度库存更新
  - 订单：查询、状态更新、创建发货单、添加跟踪号
  - 客户：按 ID/邮箱查询

## 数据模型

- `product_mappings`: Magento 与 CJ 商品/变体映射、同步状态
- `order_mappings`: Magento 与 CJ 订单映射、状态、跟踪、金额等
- `sync_logs`: 产品/库存/订单同步日志（含用户、店铺维度）
- `stores`: 多店铺能力（Magento 凭证、供应商类型与凭证）
- `users`: 基础用户表（哈希密码）
- `token_storage`: 供应商 Token（JSON）集中持久化

## 基建与安全

- 数据库: MySQL（SQLAlchemy async + Alembic 版本）
- 缓存/队列: Redis（连接池、Hash/List/Stream）
- 日志: structlog + RotatingFile（`logs/app.log`、`logs/error.log`），请求/响应/性能日志
- 中间件: 请求日志、TrustedHost、CORS、Prometheus 计数与时延
- 安全: bcrypt 密码哈希、Fernet 对称加密、可配置 SSL 校验

## 已知取舍 / 待完善

- 图片上传：为绕过 Magento “图片内容无效”错误暂不处理，需补充媒体上传链路
- 可配置商品：变体到 configurable 的建模仍为最小化实现，复杂场景待补
- 同步状态查询：`/products/sync/status` 为占位返回，需接入真实任务/队列状态
- 多店隔离：`stores` 已建模，Webhook/同步需按 `store_id` 选择凭证与隔离路由


