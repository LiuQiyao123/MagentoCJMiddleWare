"""
URL解析工具
用于从CJ Dropshipping商品链接中提取商品ID
"""
import re
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)


def extract_product_id_from_url(url: str) -> str:
    """
    从CJ商品URL中提取商品ID
    
    Args:
        url: CJ商品链接，格式如：
            https://www.cjdropshipping.com/product/...-p-1744230344494157824.html
    
    Returns:
        商品ID字符串
        
    Raises:
        ValueError: 当无法从URL中提取商品ID时
    """
    try:
        # 匹配 p-数字.html 格式
        pattern = r'p-(\d+)\.html$'
        match = re.search(pattern, url)
        
        if not match:
            # 尝试其他可能的格式
            patterns = [
                r'p-(\d+)',  # 没有.html后缀
                r'product/(\d+)',  # 直接是product/数字
                r'pid=(\d+)',  # URL参数格式
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    break
        
        if not match:
            raise ValueError(f"无法从URL中提取商品ID: {url}")
        
        product_id = match.group(1)
        logger.info("成功从URL提取商品ID", extra={"url": url, "product_id": product_id})
        
        return product_id
        
    except Exception as e:
        logger.error("URL解析失败", extra={"url": url, "error": str(e)})
        raise ValueError(f"URL解析失败: {str(e)}")


def validate_cj_url(url: str) -> bool:
    """
    验证是否为有效的CJ商品URL
    
    Args:
        url: 待验证的URL
        
    Returns:
        True表示有效，False表示无效
    """
    try:
        # 检查是否为CJ域名
        if not url.startswith(('https://www.cjdropshipping.com', 'http://www.cjdropshipping.com')):
            return False
        
        # 检查是否包含product路径
        if '/product/' not in url:
            return False
        
        # 尝试提取商品ID
        extract_product_id_from_url(url)
        return True
        
    except Exception:
        return False 