"""
CJ 变体维度到 Magento 属性的映射器
支持关键词匹配 + 模糊匹配（编辑距离）+ 自动创建属性选项
"""
import re
import pymysql
from typing import Dict, List, Optional, Tuple

import structlog

logger = structlog.get_logger(__name__)

# 已知属性及其ID（首次查询后缓存）
_attr_cache: Dict[str, int] = {}

# 选项缓存 {attr_code: {option_label: option_id}}
_option_cache: Dict[str, Dict[str, int]] = {}

# 映射规则
KEYWORD_RULES: List[Tuple[List[str], str, str]] = [
    (["color", "colour", "coloer", "clour", "颜色", "色彩", "色"], "cj_color", "CJ Color"),
    (["size", "尺寸", "大小", "尺码"], "cj_size", "CJ Size"),
    (["material", "材质", "材料"], "cj_material", "CJ Material"),
]


def _get_db():
    """获取 Magento 数据库连接"""
    return pymysql.connect(
        host="magento-db", port=3306,
        user="magento", password="magento",
        database="magento",
        charset="utf8mb4"
    )


def levenshtein_distance(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row
    return prev_row[-1]


def map_cj_key_to_magento(cj_key: str) -> Tuple[str, str]:
    """将 CJ 维度 key 映射到 Magento 属性"""
    if not cj_key:
        return ("cj_variant", "CJ Variant")
    
    key_lower = cj_key.strip().lower()
    
    for keywords, attr_code, attr_label in KEYWORD_RULES:
        # 精确匹配
        if key_lower in [k.lower() for k in keywords]:
            return (attr_code, attr_label)
        # 包含匹配
        for kw in keywords:
            if kw.lower() in key_lower or key_lower in kw.lower():
                return (attr_code, attr_label)
        # 编辑距离（≤2）
        for kw in keywords:
            kw_clean = re.sub(r'[^a-z]', '', kw.lower())
            key_clean = re.sub(r'[^a-z]', '', key_lower)
            if kw_clean and key_clean and levenshtein_distance(kw_clean, key_clean) <= 2:
                return (attr_code, attr_label)
    
    safe_code = re.sub(r'[^a-z0-9_]', '_', key_lower)[:30]
    if not safe_code.startswith("cj_"):
        safe_code = f"cj_{safe_code}" if safe_code else "cj_variant"
    return (safe_code, cj_key.strip())


def get_attribute_id(attr_code: str) -> Optional[int]:
    """获取 Magento 属性 ID"""
    if attr_code in _attr_cache:
        return _attr_cache[attr_code]
    
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT attribute_id FROM eav_attribute WHERE attribute_code=%s AND entity_type_id=4",
            (attr_code,)
        )
        row = cur.fetchone()
        if row:
            _attr_cache[attr_code] = row[0]
            return row[0]
    finally:
        conn.close()
    return None


def ensure_attribute_option(attr_code: str, option_label: str) -> Optional[int]:
    """确保属性选项存在，返回 option_id"""
    if attr_code in _option_cache and option_label in _option_cache[attr_code]:
        return _option_cache[attr_code][option_label]
    
    attr_id = get_attribute_id(attr_code)
    if not attr_id:
        logger.error("Attribute not found", extra={"code": attr_code})
        return None
    
    conn = _get_db()
    try:
        cur = conn.cursor()
        
        # 检查是否已存在
        cur.execute("""
            SELECT o.option_id FROM eav_attribute_option o
            JOIN eav_attribute_option_value v ON o.option_id = v.option_id
            WHERE o.attribute_id=%s AND v.value=%s AND v.store_id=0
            LIMIT 1
        """, (attr_id, option_label))
        row = cur.fetchone()
        if row:
            _option_cache.setdefault(attr_code, {})[option_label] = row[0]
            return row[0]
        
        # 创建新选项
        cur.nextset()
        cur.execute("INSERT INTO eav_attribute_option (attribute_id, sort_order) VALUES (%s, 0)", (attr_id,))
        cur.execute("SELECT LAST_INSERT_ID()")
        option_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO eav_attribute_option_value (option_id, store_id, value) VALUES (%s, 0, %s)",
            (option_id, option_label)
        )
        conn.commit()
        
        _option_cache.setdefault(attr_code, {})[option_label] = option_id
        logger.info("Created attribute option", extra={"attr": attr_code, "option": option_label, "id": option_id})
        return option_id
    except Exception as e:
        conn.rollback()
        logger.error("Failed to create option", extra={"attr": attr_code, "option": option_label, "error": str(e)})
        return None
    finally:
        conn.close()


def extract_dimensions(product_data: Dict, variants: List[Dict]) -> List[Tuple[str, str]]:
    """
    从 CJ 商品数据和变体中提取维度信息。
    优先使用 productKeySet，否则从 variantKey 推断。
    返回 [(attribute_code, label), ...]
    """
    dimensions = []
    
    # 1. 从 productKeySet 获取
    key_set = product_data.get("productKeySet") or product_data.get("productKey", [])
    if isinstance(key_set, str):
        try:
            import json
            key_set = json.loads(key_set)
        except:
            key_set = [key_set]
    
    if isinstance(key_set, list) and key_set:
        for key in key_set:
            attr_code, attr_label = map_cj_key_to_magento(str(key))
            if attr_code not in [d[0] for d in dimensions]:
                dimensions.append((attr_code, attr_label))
        return dimensions
    
    # 2. 从 variantKey 推断（如 "Blue-S", "A"）
    if variants:
        # 检查第一个变体的 key 是否含连字符（如 "Blue-S" = 颜色-尺寸）
        sample_key = variants[0].get("variantKey", "")
        if "-" in sample_key:
            parts = sample_key.split("-")
            labels = ["颜色", "尺寸", "规格3", "规格4"]
            for i in range(len(parts)):
                attr_code, _ = map_cj_key_to_magento(labels[i] if i < len(labels) else f"规格{i+1}")
                if attr_code not in [d[0] for d in dimensions]:
                    dimensions.append((attr_code, labels[i]))
        else:
            # 单一维度（如 "A", "B", "C"）
            dimensions.append(("cj_color", "CJ Color"))
    
    return dimensions


def parse_variant_values(vk: str, dim_count: int) -> List[str]:
    """解析 variantKey（如 "Blue-S"）为多维度值列表"""
    if not vk:
        return [""] * max(dim_count, 1)
    parts = vk.split("-")
    while len(parts) < dim_count:
        parts.append("")
    return parts[:dim_count]
