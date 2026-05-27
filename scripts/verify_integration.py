#!/usr/bin/env python3
"""
验证 Magento Integration 配置和权限
检查 Integration 是否正确创建、激活，并测试 API 访问权限
"""
import os
import sys
import pymysql
import httpx
import asyncio
from typing import Optional, Dict, List

# 从环境变量获取配置
DB_HOST = os.getenv('MAGENTO_DB_HOST', 'localhost')
DB_PORT = int(os.getenv('MAGENTO_DB_PORT', 3306))
DB_NAME = os.getenv('MAGENTO_DB_NAME', 'magento')
DB_USER = os.getenv('MAGENTO_DB_USER', 'root')
DB_PASSWORD = os.getenv('MAGENTO_DB_PASSWORD', '')

INTEGRATION_NAME = os.getenv('INTEGRATION_NAME', 'CJ_Sync')
MAGENTO_BASE_URL = os.getenv('MAGENTO_BASE_URL', 'https://shop.yokileopard.top')


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


def verify_integration_db(conn, name: str) -> Dict:
    """验证 Integration 数据库配置"""
    results = {
        'integration_exists': False,
        'integration_active': False,
        'consumer_exists': False,
        'role_exists': False,
        'role_correct': False,
        'permissions_exist': False,
        'resource_id_cleared': False,
        'token_exists': False
    }
    
    with conn.cursor() as cursor:
        # 1. 检查 Integration
        cursor.execute(
            """SELECT integration_id, name, status, consumer_id, role_id
               FROM integration WHERE name = %s""",
            (name,)
        )
        integration = cursor.fetchone()
        
        if integration:
            results['integration_exists'] = True
            results['integration_active'] = (integration['status'] == 1)
            consumer_id = integration['consumer_id']
            role_id = integration['role_id']
            
            # 2. 检查 oauth_consumer
            if consumer_id:
                cursor.execute(
                    "SELECT consumer_id, name, resource_id FROM oauth_consumer WHERE consumer_id = %s",
                    (consumer_id,)
                )
                consumer = cursor.fetchone()
                if consumer:
                    results['consumer_exists'] = True
                    results['resource_id_cleared'] = (consumer['resource_id'] is None)
            
            # 3. 检查 authorization_role
            if role_id:
                cursor.execute(
                    """SELECT role_id, role_type, user_id, user_type, role_name
                       FROM authorization_role WHERE role_id = %s""",
                    (role_id,)
                )
                role = cursor.fetchone()
                if role:
                    results['role_exists'] = True
                    # 检查 role_type 和 user_id 是否正确
                    results['role_correct'] = (
                        role['role_type'] == 'U' and
                        role['user_id'] == integration['integration_id'] and
                        role['user_type'] == 'integration'
                    )
                    
                    # 4. 检查权限规则
                    cursor.execute(
                        "SELECT COUNT(*) as count FROM authorization_rule WHERE role_id = %s",
                        (role_id,)
                    )
                    rule_count = cursor.fetchone()
                    results['permissions_exist'] = (rule_count['count'] > 0)
            
            # 5. 检查 Token
            if consumer_id:
                cursor.execute(
                    """SELECT COUNT(*) as count FROM oauth_token
                       WHERE consumer_id = %s AND type = 'access' AND revoked = 0""",
                    (consumer_id,)
                )
                token_count = cursor.fetchone()
                results['token_exists'] = (token_count['count'] > 0)
    
    return results


async def verify_api_permissions(token: str, base_url: str) -> Dict:
    """验证 API 访问权限"""
    results = {
        'basic_connection': False,
        'store_configs': False,
        'products_list': False,
        'create_product': False
    }
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
        # 1. 基础连接测试
        try:
            r = await client.get(f"{base_url}/rest/V1/directory/currency", headers=headers)
            results['basic_connection'] = (r.status_code == 200)
        except Exception as e:
            print(f"   基础连接测试失败: {e}")
        
        # 2. Store Configs
        try:
            r = await client.get(f"{base_url}/rest/V1/store/storeConfigs", headers=headers)
            results['store_configs'] = (r.status_code == 200)
        except Exception as e:
            pass
        
        # 3. Products List
        try:
            r = await client.get(
                f"{base_url}/rest/V1/products?searchCriteria[pageSize]=1",
                headers=headers
            )
            results['products_list'] = (r.status_code == 200)
        except Exception as e:
            pass
        
        # 4. Create Product (测试)
        try:
            import time
            product_data = {
                'product': {
                    'sku': f'VERIFY_TEST_{int(time.time())}',
                    'name': 'Verification Test Product',
                    'price': 10.00,
                    'status': 1,
                    'type_id': 'simple',
                    'attribute_set_id': 4,
                    'visibility': 4
                }
            }
            r = await client.post(f"{base_url}/rest/V1/products", headers=headers, json=product_data)
            results['create_product'] = (r.status_code in [200, 201])
        except Exception as e:
            pass
    
    return results


def get_token_from_db(conn, consumer_id: int) -> Optional[str]:
    """从数据库获取 Token"""
    with conn.cursor() as cursor:
        cursor.execute(
            """SELECT token FROM oauth_token
               WHERE consumer_id = %s AND type = 'access' AND revoked = 0
               ORDER BY created_at DESC LIMIT 1""",
            (consumer_id,)
        )
        result = cursor.fetchone()
        return result['token'] if result else None


def main():
    print("=" * 70)
    print("验证 Magento Integration 配置")
    print("=" * 70)
    print()
    
    # 检查数据库配置
    if not DB_PASSWORD:
        print("❌ 错误: 未设置 MAGENTO_DB_PASSWORD 环境变量")
        sys.exit(1)
    
    try:
        conn = get_db_connection()
        print("✅ 数据库连接成功")
        print()
        
        # 1. 验证数据库配置
        print("1. 验证数据库配置...")
        db_results = verify_integration_db(conn, INTEGRATION_NAME)
        
        checks = [
            ('Integration 存在', db_results['integration_exists']),
            ('Integration 已激活', db_results['integration_active']),
            ('OAuth Consumer 存在', db_results['consumer_exists']),
            ('Authorization Role 存在', db_results['role_exists']),
            ('Role 配置正确', db_results['role_correct']),
            ('权限规则存在', db_results['permissions_exist']),
            ('resource_id 已清空', db_results['resource_id_cleared']),
            ('Access Token 存在', db_results['token_exists']),
        ]
        
        for check_name, check_result in checks:
            status = "✅" if check_result else "❌"
            print(f"   {status} {check_name}")
        
        print()
        
        # 2. 验证 API 权限
        if db_results['token_exists']:
            print("2. 验证 API 访问权限...")
            
            # 获取 consumer_id
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT consumer_id FROM integration WHERE name = %s",
                    (INTEGRATION_NAME,)
                )
                integration = cursor.fetchone()
                if integration:
                    token = get_token_from_db(conn, integration['consumer_id'])
                    
                    if token:
                        api_results = asyncio.run(verify_api_permissions(token, MAGENTO_BASE_URL))
                        
                        api_checks = [
                            ('基础连接', api_results['basic_connection']),
                            ('Store Configs', api_results['store_configs']),
                            ('Products List', api_results['products_list']),
                            ('Create Product', api_results['create_product']),
                        ]
                        
                        for check_name, check_result in api_checks:
                            status = "✅" if check_result else "❌"
                            print(f"   {status} {check_name}")
                        
                        print()
                        
                        # 总结
                        all_db_ok = all([
                            db_results['integration_exists'],
                            db_results['integration_active'],
                            db_results['consumer_exists'],
                            db_results['role_exists'],
                            db_results['role_correct'],
                            db_results['permissions_exist'],
                            db_results['resource_id_cleared'],
                            db_results['token_exists']
                        ])
                        
                        all_api_ok = all([
                            api_results['basic_connection'],
                            api_results['store_configs'],
                            api_results['products_list'],
                            api_results['create_product']
                        ])
                        
                        print("=" * 70)
                        if all_db_ok and all_api_ok:
                            print("✅ 所有验证通过！Integration 配置正确且权限生效！")
                        elif all_db_ok:
                            print("⚠️  数据库配置正确，但 API 权限未完全生效")
                            print("   可能需要清除 Magento 缓存或重新生成 Token")
                        else:
                            print("❌ 数据库配置存在问题，请检查上述错误项")
                        print("=" * 70)
                    else:
                        print("   ⚠️  未找到 Access Token")
                        print("   请运行: python scripts/generate_access_token.py")
            else:
                print("   ❌ Integration 不存在")
        else:
            print("2. 跳过 API 验证（Token 不存在）")
            print("   请运行: python scripts/generate_access_token.py 生成 Token")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()


