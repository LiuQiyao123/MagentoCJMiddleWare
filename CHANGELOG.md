# Changelog — Magento-CJ Middleware

> 更新时间：2026-06-29

---

## v1.1.0 — 2026-06-29

### 新增功能

- **CJ API 分布式锁**：Redis SET NX 防止并发认证触发 CJ 429 限流
- **Token 兼容解析**：兼容 access_token/accessToken/token 多种 CJ API 返回格式
- **订单同步重构**：适配 CJ API V3 的 createOrderV3 端点，支持新的物流方案传参

### 改进

- **日志系统升级**：从 logging 迁移到 structlog，所有日志改为结构化格式（exceptions/queue/scheduler）
- **代码规范化**：统一错误报告格式、移除多余的参数展开、清理无用注释
- **API 鲁棒性**：Magento get_orders 改用 filters 参数，支持更灵活的搜索条件

### 修复

- **RedisManager.set()**：添加 nx 参数支持，修复分布式锁 TypeError
- **Cloudflare 路由**：添加 mcj.yokileopard.com 入站规则，修复 502 错误

---

## v1.0.0 — 2026-05-27

### 用户视角

### 新增功能

- **商品同步**：粘贴 CJ Dropshipping 商品链接，自动同步到 Magento
- **实时进度**：同步过程中实时显示进度条、步骤日志、错误记录
- **一键回滚**：同步失败后可一键删除本次创建的所有商品
- **任务列表**：查看历史同步任务的状态和详情
- **Web 界面**：访问 https://mcj.yokileopard.top 即可操作

### 数据同步内容

| 字段 | 来源 | 说明 |
|------|------|------|
| 商品名 | CJ productNameEn | 完整的英文商品标题 |
| 售价 | CJ suggestSellPrice | CJ 建议零售价 |
| 进货价 | CJ sellPrice | 存储在 cost_price 属性 |
| 海关编码 | CJ entryCode | HS Code |
| 申报品名 | CJ entryNameEn | 海关申报名称 |
| 商品图片 | CJ bigImage | 自动下载并上传到 Magento |
| 变体图片 | CJ variant variantImage | 每个变体对应独立图片 |
| 变体（独立商品） | CJ variants | 每个颜色/尺寸创建独立子商品 |

### 已知问题

- 变体之间没有可配置商品关联（正在开发中）
- 定价需要手动调整（后续开发 AI 定价模块）
- 图片下载较慢（后续改为并发下载）

---

## v0.x — 初始开发版

### 略
