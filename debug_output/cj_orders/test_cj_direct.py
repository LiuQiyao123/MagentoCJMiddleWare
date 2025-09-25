
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.clients.cj_client import get_cj_client

async def test_cj_orders():
    try:
        cj_client = await get_cj_client()
        
        # 获取订单列表
        print("获取订单列表...")
        orders = await cj_client.get_order_list(page=1, page_size=10)
        print(f"订单列表响应: {orders}")
        
        # 如果有订单，尝试获取第一个订单的详情
        if orders.get('data') and orders['data'].get('list'):
            first_order = orders['data']['list'][0]
            order_id = first_order.get('orderId')
            if order_id:
                print(f"获取订单详情: {order_id}")
                order_detail = await cj_client.get_order_detail(order_id)
                print(f"订单详情: {order_detail}")
                
                print(f"获取跟踪信息: {order_id}")
                tracking = await cj_client.get_tracking_info(order_id)
                print(f"跟踪信息: {tracking}")
        
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_cj_orders())
