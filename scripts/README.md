# MCJ CMS 自动配置模块

通过 Magento REST API 自动发布 CMS 页面和区块。

## 快速开始

```bash
pip install -r requirements.txt
```

```python
from cms_manager import MagentoCMS

cms = MagentoCMS(
    base_url="https://shop.yokileopard.top",
    api_token="你的Magento集成Token",
)

# 一键发布所有CMS内容
cms.apply_all()
```

## 模板列表

| 模板文件 | 包含页面 | 说明 |
|---------|---------|------|
| `policy.yaml` | 8个 | 退换货、隐私、配送、关于我们、FAQ、条款 |
| `homepage.yaml` | 2个 | 首页 + 分类页描述 |
| `contact.yaml` | 1个 | 联系我们 |

## 自动创建的内容

- Return & Refund Policy
- Privacy Policy
- Shipping Policy
- About Us
- FAQ
- Terms & Conditions
- Contact Us
- Home
- Footer Links (block)
- Category Description (block)

所有内容为英文，面向美日欧市场。配送时间按 dropshipping 模式设定（7-15工作日标准，3-7工作日加急）。

## 模板变量

模板中 {{year}} 会自动替换为当前年份，{{store_url}} 替换为商店域名。
