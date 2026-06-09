"""
Magento CMS 自动配置模块
========================
通过 Magento REST API 自动创建/更新 CMS 页面和区块。
支持多站点（多 Store）配置。

用法:
    from cms_manager import MagentoCMS

    cms = MagentoCMS(base_url="https://shop.yokileopard.top", api_token="xxx")
    cms.apply_template("policy")           # 应用政策模板
    cms.apply_all()                        # 应用所有模板
"""

import json
import logging
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

import requests
import yaml

logger = logging.getLogger("mcj_cms")


class MagentoAPIError(Exception):
    """Magento API 调用异常"""


class MagentoCMS:
    """
    Magento CMS 管理器，通过 REST API 操作页面和区块。
    """

    def __init__(
        self,
        base_url: str,
        api_token: str,
        template_dir: Optional[Path] = None,
        store_id: int = 0,
    ):
        """
        Args:
            base_url: Magento 站点地址，如 https://shop.yokileopard.top
            api_token: Magento 集成 Token (Integration Access Token)
            template_dir: YAML 模板目录，默认 ./templates
            store_id: Store ID，0 表示默认/所有商店
        """
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self.template_dir = Path(template_dir or Path(__file__).parent / "templates")
        self.store_id = store_id
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    # ─── API 基础调用 ───────────────────────────────────────────

    def _api_call(self, method: str, path: str, data: dict = None) -> dict:
        """调用 Magento REST API"""
        url = urljoin(f"{self.base_url}/", f"rest/V1/{path.lstrip('/')}")
        try:
            resp = self.session.request(method, url, json=data, timeout=30)
        except requests.RequestException as e:
            raise MagentoAPIError(f"请求失败: {e}") from e

        if resp.status_code in (200, 201):
            return resp.json() if resp.text else {}

        # 尝试解析错误信息
        try:
            err = resp.json()
            msg = err.get("message", resp.text)
        except (json.JSONDecodeError, AttributeError):
            msg = resp.text or f"HTTP {resp.status_code}"
        raise MagentoAPIError(f"Magento API 错误 ({resp.status_code}): {msg}")

    # ─── CMS Page 操作 ─────────────────────────────────────────

    def list_pages(self) -> list[dict]:
        """列出所有 CMS 页面"""
        result = self._api_call("GET", "cmsPage/search", {
            "searchCriteria": {"pageSize": 100}
        })
        return result.get("items", [])

    def get_page_by_id(self, page_id: int) -> dict:
        """按 ID 获取 CMS 页面"""
        return self._api_call("GET", f"cmsPage/{page_id}")

    def create_page(self, page_data: dict) -> dict:
        """创建 CMS 页面"""
        return self._api_call("POST", "cmsPage", {"page": page_data})

    def update_page(self, page_id: int, page_data: dict) -> dict:
        """更新 CMS 页面"""
        return self._api_call("PUT", f"cmsPage/{page_id}", {"page": page_data})

    def delete_page(self, page_id: int):
        """删除 CMS 页面"""
        self._api_call("DELETE", f"cmsPage/{page_id}")

    def find_page_by_identifier(self, identifier: str) -> Optional[dict]:
        """按 URL Key (identifier) 查找页面"""
        pages = self.list_pages()
        for p in pages:
            if p.get("identifier") == identifier:
                return p
        return None

    # ─── CMS Block 操作 ────────────────────────────────────────

    def list_blocks(self) -> list[dict]:
        """列出所有 CMS 区块"""
        result = self._api_call("GET", "cmsBlock/search", {
            "searchCriteria": {"pageSize": 100}
        })
        return result.get("items", [])

    def get_block_by_id(self, block_id: int) -> dict:
        return self._api_call("GET", f"cmsBlock/{block_id}")

    def create_block(self, block_data: dict) -> dict:
        return self._api_call("POST", "cmsBlock", {"block": block_data})

    def update_block(self, block_id: int, block_data: dict) -> dict:
        return self._api_call("PUT", f"cmsBlock/{block_id}", {"block": block_data})

    def delete_block(self, block_id: int):
        self._api_call("DELETE", f"cmsBlock/{block_id}")

    def find_block_by_identifier(self, identifier: str) -> Optional[dict]:
        blocks = self.list_blocks()
        for b in blocks:
            if b.get("identifier") == identifier:
                return b
        return None

    # ─── 模板管理 ──────────────────────────────────────────────

    def load_template(self, name: str) -> dict:
        """加载 YAML 模板文件"""
        path = self.template_dir / f"{name}.yaml"
        if not path.exists():
            raise FileNotFoundError(f"模板不存在: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def list_templates(self) -> list[str]:
        """列出所有可用模板"""
        files = self.template_dir.glob("*.yaml")
        return sorted(f.stem for f in files)

    def apply_template(self, name: str, store_id: int = None):
        """
        应用指定模板到 Magento。

        模板 YAML 格式:
        ---
        title: 商店名称
        identifier: home  # 对应 CMS URL Key
        type: page         # page | block
        content: |
          <h1>欢迎光临</h1>
          <p>{{store_name}}</p>
        store_id: 0
        active: true

        title: 退换货政策
        identifier: return-policy
        type: page
        content: |
          <h2>退换货政策</h2>
          ...
        """
        template = self.load_template(name)
        store_id = store_id if store_id is not None else self.store_id
        results = []

        # 模板可以包含多个条目（列表格式）或单个
        items = template if isinstance(template, list) else [template]

        for item in items:
            item_type = item.get("type", "page")
            identifier = item.get("identifier", "")
            title = item.get("title", identifier)
            content = item.get("content", "")
            active = item.get("active", True)
            item_store_id = item.get("store_id", store_id)

            # 替换内容中的占位符
            content = self._render_content(content, item)

            if item_type == "page":
                result = self._upsert_page(
                    identifier=identifier,
                    title=title,
                    content=content,
                    active=active,
                    store_id=item_store_id,
                )
            elif item_type == "block":
                result = self._upsert_block(
                    identifier=identifier,
                    title=title,
                    content=content,
                    active=active,
                    store_id=item_store_id,
                )
            else:
                logger.warning(f"未知类型: {item_type}")
                continue

            results.append(result)
            logger.info(f"  ✅ {item_type}: {identifier} ({title})")

        return results

    def apply_all(self, store_id: int = None):
        """应用所有可用模板"""
        templates = self.list_templates()
        logger.info(f"共找到 {len(templates)} 个模板，开始应用...")
        results = {}
        for name in templates:
            logger.info(f"→ 应用模板: {name}")
            try:
                results[name] = self.apply_template(name, store_id)
            except Exception as e:
                logger.error(f"  ❌ {name}: {e}")
                results[name] = {"error": str(e)}
        return results

    # ─── 内部方法 ──────────────────────────────────────────────

    def _render_content(self, content: str, item: dict) -> str:
        """替换内容中的模板变量"""
        placeholders = {
            "store_name": item.get("title", ""),
            "year": str(time.gmtime().tm_year),
            "store_url": self.base_url,
        }
        for key, value in placeholders.items():
            content = content.replace(f"{{{{{key}}}}}", value)
        return content

    def _upsert_page(
        self,
        identifier: str,
        title: str,
        content: str,
        active: bool = True,
        store_id: int = 0,
    ) -> dict:
        """创建或更新 CMS 页面"""
        existing = self.find_page_by_identifier(identifier)
        page_data = {
            "title": title,
            "identifier": identifier,
            "content": content,
            "active": int(active),
            "store_id": [store_id],
            "page_layout": "1column",
            "meta_title": title,
        }

        if existing:
            page_id = existing["id"]
            page_data["id"] = page_id
            return self.update_page(page_id, page_data)
        else:
            return self.create_page(page_data)

    def _upsert_block(
        self,
        identifier: str,
        title: str,
        content: str,
        active: bool = True,
        store_id: int = 0,
    ) -> dict:
        """创建或更新 CMS 区块"""
        existing = self.find_block_by_identifier(identifier)
        block_data = {
            "title": title,
            "identifier": identifier,
            "content": content,
            "active": int(active),
            "store_id": [store_id],
        }

        if existing:
            block_id = existing["id"]
            block_data["id"] = block_id
            return self.update_block(block_id, block_data)
        else:
            return self.create_block(block_data)
