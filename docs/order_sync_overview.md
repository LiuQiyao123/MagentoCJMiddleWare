# Magento ⇄ CJ Middleware 订单同步文档

> 最新更新时间：2025-10-23

## 1. 系统目标
1. 顾客在 Magento 下单后 < 1 min 自动推送到 middleware，并创建 CJ 订单。
2. 每 15 min 轮询 CJ API，将订单状态 / 物流信息回写 Magento，保证 ≤ 15 min 时效。
3. 支持多店加盟与多供应商扩展，商品同步带分类缓存。  

---

## 2. 模块架构
```
Magento Webhook   ──────────────▶  FastAPI /webhooks/magento/order
                                               │
                                               ▼
                                         Redis Stream (stream:orders)
                                               │
   APScheduler ◀─────────────┐     Worker(order_worker.py)
                             │             │
             poll_cj_status  │             ▼
                             │      ExternalSupplierGateway
                             │          (CJGateway)
                             ▼             │
                         OrderSyncService  │
                              │            ▼
                              └──▶ Magento REST API
```
- **Webhook**：接收 `order_created` 事件，验签后写入 Redis Stream。
- **Worker**：消费 Stream，调用 `CJGateway.create_order()`，写入 `order_mappings`。
- **Scheduler**：每 `SYNC_INTERVAL_MINUTES` 运行 `poll_cj_status()`，查询 CJ 订单状态并回写 Magento。  

---

## 3. 数据模型
| 表            | 功能 | 关键字段 |
|---------------|------|----------|
| stores        | 加盟店凭证与配置 | `name`, `magento_base_url`, `supplier_type`, `supplier_credentials` |
| order_mappings| Magento 与 CJ 订单 ID 映射 | `magento_order_id`, `cj_order_id`, `order_status`, `tracking_number` |
| sync_log      | 同步操作流水 | `sync_type`, `status`, `message`, `details` |

> 迁移脚本：`alembic/versions/20251023_create_store_and_order_mapping.py`  
> 上线前运行：`alembic upgrade head`

---

## 4. 主要代码
| 位置 | 说明 |
|------|------|
| `app/api/v1/webhooks.py` | Webhook 端点，验签 & 入队 |
| `app/services/order_worker.py` | Redis Stream 消费者，创建 CJ 订单 |
| `app/services/scheduler.py` | APScheduler 任务，轮询 CJ 状态 |
| `app/gateways/base.py` | `ExternalSupplierGateway` 抽象接口 |
| `app/gateways/cj_gateway.py` | CJ Dropshipping 实现 |
| `app/models/store.py` | Store 表 ORM |
| `app/models/order.py` | OrderMapping 表 ORM |

---

## 5. 运行组件
```bash
# 1. 启动 API
uvicorn app.main:app --reload

# 2. 启动 Worker（可多个实例并行）
python -m app.services.order_worker

# 3. 启动 Scheduler
python -m app.services.scheduler
```
容器化部署时，可分别定义三个服务或使用 `supervisord`。

---

## 6. 环境变量关键项
| 变量 | 作用 |
|------|------|
| `MAGENTO_WEBHOOK_SECRET` | HMAC 共享密钥，用于验证 Magento Webhook |
| `SYNC_INTERVAL_MINUTES` | CJ 轮询周期（默认 15） |
| `REDIS_HOST/PORT` | Redis 连接信息 |
| `CJ_API_EMAIL / CJ_API_KEY` | CJ Dropshipping 凭证 |

---

## 7. 常见运维命令
```bash
# 查看 Redis Stream 长度
redis-cli XLEN stream:orders

# 查看 APScheduler 任务
curl http://localhost:8000/monitor
```

---

## 8. 未来扩展
1. **多供应商**：实现 `AliExpressGateway` 并在 `gateways/factory.py` 注册即可。
2. **多店**：在 Webhook Header 传 `X-Store-Id`，Worker 根据 `store_id` 读取对应凭证。
3. **失败重试 / 死信队列**：Redis Stream 支持消息未 ACK 自动积压，可加后台任务定期处理失败记录。

---

## 9. TODO 追踪
请参考项目根目录 `order.plan.md` 与 `.todo` 列表，保持文档与代码同步。
