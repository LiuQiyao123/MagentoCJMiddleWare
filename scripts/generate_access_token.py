#!/usr/bin/env python3
"""
生成和获取 Magento Integration Access Token
通过数据库查询或生成 Access Token
"""
import os
import sys
import pymysql
import secrets
from typing import Optional, Dict
from datetime import datetime, timedelta

# 从环境变量获取配置
DB_HOST = os.getenv('MAGENTO_DB_HOST', 'localhost')
DB_PORT = int(os.getenv('MAGENTO_DB_PORT', 3306))
DB_NAME = os.getenv('MAGENTO_DB_NAME', 'magento')
DB_USER = os.getenv('MAGENTO_DB_USER', 'root')
DB_PASSWORD = os.getenv('MAGENTO_DB_PASSWORD', '')

INTEGRATION_NAME = os.getenv('INTEGRATION_NAME', 'CJ_Sync')


def get_db_connection():
    """获取数据库连接"""
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        sys.exit(1)


def get_integration_info(conn, name: str) -> Optional[Dict]:
    """获取 Integration 信息"""
    with conn.cursor() as cursor:
        cursor.execute(
            """SELECT i.integration_id, i.name, i.status, i.consumer_id, i.role_id
               FROM integration i
               WHERE i.name = %s""",
            (name,)
        )
        result = cursor.fetchone()
        return result


def get_existing_token(conn, consumer_id: int) -> Optional[str]:
    """获取现有的 Access Token"""
    with conn.cursor() as cursor:
        # 查找未过期的 Token (type = 'access')
        cursor.execute(
            """SELECT token, expires
               FROM oauth_token
               WHERE consumer_id = %s AND type = 'access' AND revoked = 0
               ORDER BY created_at DESC
               LIMIT 1""",
            (consumer_id,)
        )
        result = cursor.fetchone()
        
        if result:
            token = result['token']
            expires = result['expires']
            
            # 检查 Token 是否过期
            if expires:
                expires_dt = datetime.fromtimestamp(int(expires))
                if expires_dt > datetime.now():
                    return token
                else:
                    print(f"  ⚠️  现有 Token 已过期 (过期时间: {expires_dt})")
                    return None
            else:
                # 如果没有过期时间，假设 Token 有效
                return token
        
        return None


def generate_new_token(conn, consumer_id: int) -> str:
    """生成新的 Access Token"""
    # 生成 32 位随机 Token
    token = secrets.token_urlsafe(32)[:32]  # 确保是 32 位
    
    # 计算过期时间（通常 Access Token 有效期为 1 小时，但 Magento 可能不同）
    # 这里设置为 1 年后过期（实际上 Magento Integration Token 通常不会过期）
    expires = int((datetime.now() + timedelta(days=365)).timestamp())
    
    with conn.cursor() as cursor:
        # 先撤销所有旧的 Token
        cursor.execute(
            "UPDATE oauth_token SET revoked = 1 WHERE consumer_id = %s AND type = 'access'",
            (consumer_id,)
        )
        
        # 插入新的 Token
        cursor.execute(
            """INSERT INTO oauth_token (consumer_id, type, token, secret, verifier, callback_url, revoked, expires, created_at)
               VALUES (%s, 'access', %s, '', '', '', 0, %s, NOW())""",
            (consumer_id, token, expires)
        )
        conn.commit()
        
        print(f"  ✅ 已生成新的 Access Token")
        return token


def main():
    print("=" * 70)
    print("生成/获取 Magento Integration Access Token")
    print("=" * 70)
    print()
    
    # 检查数据库配置
    if not DB_PASSWORD:
        print("❌ 错误: 未设置 MAGENTO_DB_PASSWORD 环境变量")
        print()
        print("使用方法:")
        print("  export MAGENTO_DB_HOST=localhost")
        print("  export MAGENTO_DB_PORT=3306")
        print("  export MAGENTO_DB_NAME=magento")
        print("  export MAGENTO_DB_USER=root")
        print("  export MAGENTO_DB_PASSWORD=your_password")
        print("  export INTEGRATION_NAME=CJ_Sync")
        print("  python scripts/generate_access_token.py")
        sys.exit(1)
    
    print(f"配置:")
    print(f"  Integration Name: {INTEGRATION_NAME}")
    print(f"  Database: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    print()
    
    try:
        conn = get_db_connection()
        print("✅ 数据库连接成功")
        print()
        
        # 1. 检查 Integration
        print("1. 检查 Integration...")
        integration = get_integration_info(conn, INTEGRATION_NAME)
        if not integration:
            print(f"❌ Integration '{INTEGRATION_NAME}' 不存在")
            print("   请先运行 scripts/create_integration_via_db.py 创建 Integration")
            sys.exit(1)
        
        if integration['status'] != 1:
            print(f"⚠️  Integration 未激活 (status: {integration['status']})")
            print("   请先运行 scripts/activate_integration.py 激活 Integration")
            sys.exit(1)
        
        print(f"   integration_id: {integration['integration_id']}")
        print(f"   consumer_id: {integration['consumer_id']}")
        print()
        
        # 2. 检查现有 Token
        print("2. 检查现有 Token...")
        existing_token = get_existing_token(conn, integration['consumer_id'])
        
        if existing_token:
            print(f"   ✅ 找到现有 Token: {existing_token[:20]}...")
            print()
            print("=" * 70)
            print("✅ 使用现有 Token")
            print("=" * 70)
            print()
            print(f"Token: {existing_token}")
            print()
            print("下一步:")
            print("1. 更新 .env 文件:")
            print(f"   MAGENTO_API_TOKEN={existing_token}")
            print()
            print("2. 重启应用:")
            print("   docker-compose restart app")
            print()
        else:
            # 3. 生成新 Token
            print("   未找到有效 Token，生成新 Token...")
            print()
            print("3. 生成新 Token...")
            new_token = generate_new_token(conn, integration['consumer_id'])
            print()
            
            print("=" * 70)
            print("✅ 新 Token 已生成")
            print("=" * 70)
            print()
            print(f"Token: {new_token}")
            print()
            print("下一步:")
            print("1. 更新 .env 文件:")
            print(f"   MAGENTO_API_TOKEN={new_token}")
            print()
            print("2. 重启应用:")
            print("   docker-compose restart app")
            print()
            print("3. 测试 Token:")
            print("   docker-compose exec app python -c \"")
            print("   import os, httpx, asyncio")
            print("   async def test():")
            print("       token = os.getenv('MAGENTO_API_TOKEN')")
            print("       async with httpx.AsyncClient(verify=False) as client:")
            print("           r = await client.get('https://shop.yokileopard.top/rest/V1/products?searchCriteria[pageSize]=1',")
            print("               headers={'Authorization': f'Bearer {token}'})")
            print("           print(f'Status: {r.status_code}')")
            print("   asyncio.run(test())")
            print("   \"")
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()


