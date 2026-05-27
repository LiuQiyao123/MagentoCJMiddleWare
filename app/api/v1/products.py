"""
产品API路由
"""
import asyncio
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
import structlog
import json

from app.services.product_sync import get_product_sync_service, ProductSyncService
from app.services.task_manager import task_manager
from app.clients.cj_client import get_cj_client, CJClient
from app.utils.url_parser import extract_product_id_from_url, validate_cj_url

logger = structlog.get_logger(__name__)
router = APIRouter()


class ProductSyncSingleRequest(BaseModel):
    """单个产品同步请求模型"""
    product_url: str = Field(..., description="CJ商品链接")


class InventorySyncRequest(BaseModel):
    """库存同步请求模型"""
    product_ids: Optional[list] = Field(None, description="产品ID列表")


@router.post("/sync/single")
async def sync_single_product(
    request: ProductSyncSingleRequest,
    product_sync_service: ProductSyncService = Depends(get_product_sync_service)
):
    """异步同步单个CJ商品到Magento（立即返回task_id）"""
    try:
        if not validate_cj_url(request.product_url):
            return {"success": False, "error": "无效的CJ商品链接", "error_code": "1001"}

        try:
            product_id = extract_product_id_from_url(request.product_url)
        except ValueError as e:
            return {"success": False, "error": str(e), "error_code": "1002"}

        # 创建异步任务
        task_id = await task_manager.create_task("product_sync", {
            "product_id": product_id,
            "product_url": request.product_url
        })

        # 后台执行同步
        asyncio.create_task(_run_sync(task_id, product_id, request.product_url, product_sync_service))

        return {"success": True, "task_id": task_id, "message": "同步任务已启动"}

    except Exception as e:
        logger.error("启动同步失败", extra={"error": str(e)})
        return {"success": False, "error": str(e), "error_code": "5001"}


async def _run_sync(task_id: str, product_id: str, product_url: str, service: ProductSyncService):
    """后台执行同步任务（支持可配置商品）"""
    from app.services.attribute_mapper import (
        extract_dimensions, ensure_attribute_option,
        parse_variant_values, get_attribute_id
    )
    
    try:
        await task_manager.update_progress(task_id, 5, "开始同步...")

        # 1. 获取CJ商品
        await task_manager.update_progress(task_id, 10, "正在获取CJ商品信息...", f"[CJ] 获取商品 {product_id}")
        cj_response = await service.cj_client.get_product_detail(product_id)
        if not cj_response or not cj_response.get("result"):
            raise ValueError(f"商品不存在或获取失败: {product_id}")
        cj_product = cj_response.get("data", {})
        await task_manager.update_progress(task_id, 20, "CJ商品信息获取成功", f"[CJ] 商品名: {(cj_product.get('productNameEn') or '')[:60]}")

        # 2. 获取变体
        await task_manager.update_progress(task_id, 25, "正在获取商品变体...")
        root_variants = cj_product.get("variants", [])
        if not root_variants:
            variant_response = await service.cj_client.get_product_variants(product_id)
            if variant_response.get("result"):
                vd = variant_response.get("data", [])
                root_variants = vd if isinstance(vd, list) else vd.get("list", [])
        await task_manager.update_progress(task_id, 30, f"找到 {len(root_variants)} 个变体", f"[CJ] 变体数: {len(root_variants)}")

        # 3. 提取维度 & 创建属性选项
        dimensions = extract_dimensions(cj_product, root_variants)
        has_multiple_dims = len(dimensions) > 0 and len(root_variants) > 1
        
        if has_multiple_dims:
            await task_manager.update_progress(task_id, 33, f"检测到 {len(dimensions)} 个变体维度", f"[属性] 维度: {[d[0] for d in dimensions]}")
            # 为所有维度创建选项
            dim_count = len(dimensions)
            for v in root_variants:
                vals = parse_variant_values(v.get("variantKey", ""), dim_count)
                for i, val in enumerate(vals):
                    if val.strip():
                        ensure_attribute_option(dimensions[i][0], val.strip())
            await task_manager.update_progress(task_id, 35, "属性选项就绪")

        # 4. 构建主商品
        name = cj_product.get("productNameEn", "") or str(cj_product.get("productName", ""))
        cj_price = service._parse_range_value(cj_product.get("suggestSellPrice", cj_product.get("sellPrice", 0)))
        cj_weight = service._parse_range_value(cj_product.get("productWeight", 0))
        cj_desc = cj_product.get("description", "") or name
        
        main_sku = f"CJ_{product_id}"
        main_product = service._build_magento_product(cj_product, root_variants)
        image_url = main_product.pop("_image_url", None)
        
        # 如果有多维度，创建为可配置商品
        if has_multiple_dims:
            main_product["type_id"] = "configurable"
            main_product["visibility"] = 4
            main_product["name"] = name[:200]
            # 关联维度属性
            dim_attr_ids = [get_attribute_id(d[0]) for d in dimensions if get_attribute_id(d[0])]
            if dim_attr_ids:
                main_product["extension_attributes"] = {
                    "configurable_product_options": [
                        {
                            "attribute_id": str(aid),
                            "label": dimensions[i][1],
                            "position": i,
                            "values": []
                        }
                        for i, aid in enumerate(dim_attr_ids) if aid
                    ]
                }
        
        await task_manager.update_progress(task_id, 38, "正在创建Magento主商品...", "[Magento] 创建主商品")
        magento_result = await service.magento_client.create_product(main_product)
        mid = magento_result.get("id")
        await task_manager.update_progress(task_id, 45, f"主商品创建成功 (ID: {mid})", f"[Magento] 主商品ID: {mid}, SKU: {main_sku}")
        
        created_skus = [main_sku]
        created_ids = [str(mid)]

        # 5. 上传主图
        if image_url:
            await task_manager.update_progress(task_id, 48, "正在上传主图...", "[图片] 下载并上传主图")
            try:
                await service._upload_product_image(main_sku, image_url)
                await task_manager.update_progress(task_id, 50, "主图上传完成", "[图片] 主图上传成功")
            except Exception as e:
                await task_manager.add_error(task_id, f"主图上传失败: {str(e)[:100]}")

        # 6. 创建变体子商品
        children = []
        child_ids = []
        dim_count = len(dimensions) if has_multiple_dims else 0
        
        if root_variants:
            total_variants = len(root_variants)
            await task_manager.update_progress(task_id, 55, f"开始创建 {total_variants} 个变体...")
            
            for idx, variant in enumerate(root_variants):
                try:
                    vk = variant.get("variantKey", str(idx))
                    child_sku = f"CJ_{product_id}_{vk}"
                    
                    # 构建自定义属性（含维度值）
                    cust_attrs = [
                        {"attribute_code": "description", "value": cj_desc},
                        {"attribute_code": "short_description", "value": f"{name[:100]} - {vk}"},
                    ]
                    
                    variant_name_suffix = vk
                    if has_multiple_dims:
                        vals = parse_variant_values(vk, dim_count)
                        dim_attr_ids = [get_attribute_id(d[0]) for d in dimensions]
                        for i, val in enumerate(vals):
                            if val.strip() and i < len(dim_attr_ids) and dim_attr_ids[i]:
                                oid = ensure_attribute_option(dimensions[i][0], val.strip())
                                if oid:
                                    cust_attrs.append({
                                        "attribute_code": dimensions[i][0],
                                        "value": str(oid)
                                    })
                        variant_name_suffix = "-".join(v.strip() for v in vals if v.strip())
                    
                    child_data = {
                        "sku": child_sku,
                        "name": f"{name[:150]} - {variant_name_suffix}"[:200],
                        "price": cj_price,
                        "status": 1,
                        "visibility": 1,
                        "type_id": "simple",
                        "attribute_set_id": 4,
                        "weight": max(cj_weight, 0.001),
                        "extension_attributes": {},
                        "custom_attributes": cust_attrs
                    }
                    
                    child_result = await service.magento_client.create_product(child_data)
                    child_sku_created = child_result.get("sku", child_sku)
                    child_id = child_result.get("id")
                    children.append({"sku": child_sku_created, "variant_key": vk, "id": child_id})
                    child_ids.append(child_id)
                    created_skus.append(child_sku_created)
                    created_ids.append(str(child_id))

                    # 上传变体图
                    vimg = variant.get("variantImage", "")
                    if vimg:
                        try:
                            await service._upload_product_image(child_sku_created, vimg, f"{name[:30]} - {vk}")
                        except Exception as ime:
                            await task_manager.add_error(task_id, f"变体 {vk} 图片上传失败: {str(ime)[:80]}")

                    pct = 55 + int((idx + 1) / total_variants * 40)
                    await task_manager.update_progress(task_id, pct, f"变体 {variant_name_suffix} ({idx+1}/{total_variants}) 完成")
                    await asyncio.sleep(0.3)

                except Exception as ve:
                    err_msg = str(ve)[:80]
                    await task_manager.add_error(task_id, f"变体 {variant.get('variantKey', str(idx))} 创建失败: {err_msg}")

        # 7. 关联子商品到可配置商品
        if has_multiple_dims and child_ids and dim_attr_ids:
            try:
                await task_manager.update_progress(task_id, 96, "正在关联子商品...", "[Magento] 关联变体到可配置商品")
                
                # 获取可配置商品当前数据
                link_data = {
                    "product": {
                        "sku": main_sku,
                        "extension_attributes": {
                            "configurable_product_options": [
                                {
                                    "attribute_id": str(aid),
                                    "label": dimensions[i][1],
                                    "position": i,
                                    "values": []
                                }
                                for i, aid in enumerate(dim_attr_ids) if aid
                            ],
                            "configurable_product_links": child_ids
                        }
                    }
                }
                await service.magento_client._make_request(
                    "PUT", f"/products/{main_sku}", data=link_data
                )
                await task_manager.update_progress(task_id, 98, "子商品关联完成")
            except Exception as le:
                await task_manager.add_error(task_id, f"关联子商品失败: {str(le)[:100]}")

        # 存储创建的SKU清单
        await task_manager.update_data(task_id, {"created_skus": created_skus, "created_ids": created_ids})

        from app.config.settings import get_settings
        settings = get_settings()
        result = {
            "product_name": name[:80], "magento_id": mid, "sku": main_sku,
            "product_type": "configurable" if has_multiple_dims and len(root_variants) > 1 else "simple",
            "variants": len(children),
            "dimensions": [d[0] for d in dimensions] if has_multiple_dims else [],
            "magento_url": f"{settings.MAGENTO_BASE_URL}/admin/catalog/product/edit/id/{mid}",
            "created_skus": created_skus,
            "created_ids": created_ids
        }
        await task_manager.mark_success(task_id, result)
        variant_msg = f"主商品+{len(children)}个变体"
        if has_multiple_dims:
            variant_msg += f" (可配置商品, {len(dimensions)}维)"
        await task_manager.update_progress(task_id, 100, f"同步完成! {variant_msg}")

    except Exception as e:
        await task_manager.mark_failed(task_id, str(e)[:200])
        logger.error("后台同步失败", extra={"task_id": task_id, "error": str(e)})


@router.post("/sync/inventory")
async def sync_inventory(
    request: InventorySyncRequest,
    product_sync_service: ProductSyncService = Depends(get_product_sync_service)
):
    """同步库存信息"""
    try:
        result = await product_sync_service.sync_inventory(request.product_ids)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error("库存同步失败", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync/status/{task_id}")
async def get_sync_status(task_id: str):
    """获取同步任务状态"""
    task = await task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return {
        "task_id": task["task_id"],
        "task_type": task["task_type"],
        "status": task["status"],
        "progress": int(task["progress"]),
        "message": task["message"],
        "errors": json.loads(task.get("errors", "[]")),
        "logs": json.loads(task.get("logs", "[]")),
        "result": json.loads(task["result"]) if task.get("result") else None,
        "created_at": task["created_at"],
        "updated_at": task["updated_at"]
    }


@router.get("/tasks")
async def list_tasks():
    """获取最近任务列表"""
    tasks = await task_manager.list_tasks(limit=50)
    return {"tasks": tasks}


@router.delete("/tasks/{task_id}/cleanup")
async def cleanup_task(task_id: str):
    """删除任务中所有已创建的商品（回滚）"""
    from app.services.product_sync import get_product_sync_service
    service = await get_product_sync_service()

    task = await task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 获取创建的SKU列表
    task_data = json.loads(task.get("task_data", "{}"))
    created_skus = task_data.get("created_skus", [])
    if not created_skus:
        # 尝试从result中获取
        result = json.loads(task.get("result", "{}")) if task.get("result") else {}
        created_skus = result.get("created_skus", [])

    if not created_skus:
        return {"success": False, "message": "无可清理的商品数据", "deleted": 0}

    deleted = 0
    errors = []
    for sku in reversed(created_skus):  # 先删变体，再删主商品
        try:
            await service.magento_client.delete_product(sku)
            deleted += 1
        except Exception as e:
            errors.append({"sku": sku, "error": str(e)[:60]})

    # 更新任务状态
    await task_manager.update_progress(task_id, 0, f"已清理 {deleted}/{len(created_skus)} 个商品")
    await task_manager.mark_failed(task_id, f"用户已回滚，删除了 {deleted} 个商品")

    return {
        "success": True,
        "deleted": deleted,
        "total": len(created_skus),
        "errors": errors,
        "message": f"已删除 {deleted}/{len(created_skus)} 个商品"
    }
