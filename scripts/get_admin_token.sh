#!/bin/bash
# 获取 Magento 管理员 Token 的脚本
# 使用方法: ./scripts/get_admin_token.sh

MAGENTO_URL="${MAGENTO_BASE_URL:-https://shop.yokileopard.top}"
ADMIN_USER="${1:-admin}"
ADMIN_PASSWORD="${2:-admin123}"

echo "=========================================="
echo "获取 Magento 管理员 Token"
echo "=========================================="
echo ""
echo "Magento URL: $MAGENTO_URL"
echo "管理员用户名: $ADMIN_USER"
echo ""
echo "正在获取 Token..."
echo ""

# 通过 REST API 获取管理员 Token
TOKEN=$(curl -s -X POST "${MAGENTO_URL}/rest/V1/integration/admin/token" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"${ADMIN_USER}\",
    \"password\": \"${ADMIN_PASSWORD}\"
  }")

# 检查是否成功
if [[ $TOKEN == *"message"* ]]; then
    echo "❌ 获取 Token 失败:"
    echo "$TOKEN" | python3 -m json.tool 2>/dev/null || echo "$TOKEN"
    echo ""
    echo "可能的原因："
    echo "  1. 用户名或密码错误"
    echo "  2. Magento API 端点不可用"
    echo "  3. 需要先创建管理员账户"
    exit 1
else
    # 清理 Token（移除引号）
    TOKEN=$(echo "$TOKEN" | tr -d '"')
    echo "✅ Token 获取成功！"
    echo ""
    echo "Token: $TOKEN"
    echo ""
    echo "=========================================="
    echo "下一步："
    echo "=========================================="
    echo ""
    echo "1. 更新 .env 文件："
    echo "   MAGENTO_API_TOKEN=$TOKEN"
    echo ""
    echo "2. 重启应用："
    echo "   docker-compose restart app"
    echo ""
    echo "3. 测试权限："
    echo "   docker-compose exec app python -c \""
    echo "   import os, httpx, asyncio"
    echo "   async def test():"
    echo "       token = os.getenv('MAGENTO_API_TOKEN')"
    echo "       async with httpx.AsyncClient(verify=False) as client:"
    echo "           r = await client.get('${MAGENTO_URL}/rest/V1/products?searchCriteria[pageSize]=1',"
    echo "               headers={'Authorization': f'Bearer {token}'})"
    echo "           print(f'Status: {r.status_code}')"
    echo "   asyncio.run(test())"
    echo "   \""
    echo ""
    echo "⚠️  注意：管理员 Token 有完整权限，安全性较低，仅作为临时解决方案。"
    echo "=========================================="
fi


