#!/usr/bin/env python3
"""
通过数据库直接创建 Magento Integration
需要数据库访问权限
"""
import os
import sys
import pymysql
from typing import List, Dict, Optional

# 从环境变量或参数获取配置
DB_HOST = os.getenv('MAGENTO_DB_HOST', 'localhost')
DB_PORT = int(os.getenv('MAGENTO_DB_PORT', 3306))
DB_NAME = os.getenv('MAGENTO_DB_NAME', 'magento')
DB_USER = os.getenv('MAGENTO_DB_USER', 'root')
DB_PASSWORD = os.getenv('MAGENTO_DB_PASSWORD', '')

INTEGRATION_NAME = 'CJ_Sync'
INTEGRATION_EMAIL = os.getenv('INTEGRATION_EMAIL', 'cj_sync@example.com')

# 必需的权限资源列表
REQUIRED_RESOURCES = [
    'Magento_Catalog::products',
    'Magento_Catalog::categories',
    'Magento_Backend::store',
    'Magento_Backend::config',
    'Magento_InventoryApi::inventory',
    'Magento_Sales::sales',
    'Magento_Sales::sales_operation',
]


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


def check_existing_integration(conn, name: str) -> Optional[Dict]:
    """检查 Integration 是否已存在"""
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT integration_id, name, status, consumer_id, role_id FROM integration WHERE name = %s",
            (name,)
        )
        result = cursor.fetchone()
        return result


def create_oauth_consumer(conn, name: str) -> int:
    """创建 oauth_consumer 记录"""
    with conn.cursor() as cursor:
        # 检查是否已存在
        cursor.execute("SELECT consumer_id FROM oauth_consumer WHERE name = %s", (name,))
        existing = cursor.fetchone()
        if existing:
            print(f"  ✅ oauth_consumer 已存在 (consumer_id: {existing['consumer_id']})")
            return existing['consumer_id']
        
        # 生成 consumer_key 和 consumer_secret
        import secrets
        consumer_key = secrets.token_urlsafe(32)
        consumer_secret = secrets.token_urlsafe(32)
        
        cursor.execute(
            """INSERT INTO oauth_consumer (name, key, secret, callback_url, rejected_callback_url, created_at)
               VALUES (%s, %s, %s, '', '', NOW())""",
            (name, consumer_key, consumer_secret)
        )
        conn.commit()
        consumer_id = cursor.lastrowid
        print(f"  ✅ 创建 oauth_consumer (consumer_id: {consumer_id})")
        return consumer_id


def create_authorization_role(conn, role_name: str, integration_id: int) -> int:
    """创建 authorization_role 记录"""
    with conn.cursor() as cursor:
        # 检查是否已存在
        cursor.execute("SELECT role_id FROM authorization_role WHERE role_name = %s", (role_name,))
        existing = cursor.fetchone()
        if existing:
            role_id = existing['role_id']
            # 更新现有 role 的 user_id 和 user_type
            cursor.execute(
                """UPDATE authorization_role 
                   SET role_type = 'U', user_id = %s, user_type = 'integration'
                   WHERE role_id = %s""",
                (integration_id, role_id)
            )
            conn.commit()
            print(f"  ✅ authorization_role 已存在，已更新 (role_id: {role_id})")
            return role_id
        
        # 创建 role，role_type 应该是 'U' (User)，user_id 关联到 integration_id
        cursor.execute(
            """INSERT INTO authorization_role (parent_id, tree_level, sort_order, role_type, user_id, user_type, role_name)
               VALUES (0, 1, 0, 'U', %s, 'integration', %s)""",
            (integration_id, role_name)
        )
        conn.commit()
        role_id = cursor.lastrowid
        print(f"  ✅ 创建 authorization_role (role_id: {role_id}, role_type: U, user_id: {integration_id})")
        return role_id


def create_authorization_rules(conn, role_id: int, resources: List[str]):
    """创建 authorization_rule 记录（权限规则）"""
    with conn.cursor() as cursor:
        for resource_id in resources:
            # 检查是否已存在
            cursor.execute(
                "SELECT rule_id FROM authorization_rule WHERE role_id = %s AND resource_id = %s",
                (role_id, resource_id)
            )
            existing = cursor.fetchone()
            if existing:
                print(f"  ✅ 权限规则已存在: {resource_id}")
                continue
            
            # 创建权限规则
            cursor.execute(
                """INSERT INTO authorization_rule (role_id, resource_id, privileges, permission)
                   VALUES (%s, %s, NULL, 'allow')""",
                (role_id, resource_id)
            )
            print(f"  ✅ 创建权限规则: {resource_id}")
        conn.commit()


def create_integration(conn, name: str, email: str, consumer_id: int, role_id: int) -> int:
    """创建 integration 记录"""
    with conn.cursor() as cursor:
        # 检查是否已存在
        existing = check_existing_integration(conn, name)
        if existing:
            print(f"  ✅ Integration 已存在 (integration_id: {existing['integration_id']})")
            # 更新现有记录（保留原有的 role_id 如果已设置）
            if role_id == 0:
                # 如果传入的 role_id 是 0，保留原有的 role_id
                cursor.execute(
                    """UPDATE integration 
                       SET email = %s, status = 0, consumer_id = %s, updated_at = NOW()
                       WHERE name = %s""",
                    (email, consumer_id, name)
                )
            else:
                cursor.execute(
                    """UPDATE integration 
                       SET email = %s, status = 0, consumer_id = %s, role_id = %s, updated_at = NOW()
                       WHERE name = %s""",
                    (email, consumer_id, role_id, name)
                )
            conn.commit()
            return existing['integration_id']
        
        # 创建新记录
        cursor.execute(
            """INSERT INTO integration (name, email, status, consumer_id, role_id, setup_type, identity_link_url, created_at, updated_at)
               VALUES (%s, %s, 0, %s, %s, 0, '', NOW(), NOW())""",
            (name, email, consumer_id, role_id)
        )
        conn.commit()
        integration_id = cursor.lastrowid
        print(f"  ✅ 创建 integration (integration_id: {integration_id})")
        return integration_id


def clear_oauth_consumer_resource_id(conn, consumer_id: int):
    """清空 oauth_consumer 的 resource_id（让 Magento 使用 role 的权限）"""
    with conn.cursor() as cursor:
        cursor.execute(
            "UPDATE oauth_consumer SET resource_id = NULL WHERE consumer_id = %s",
            (consumer_id,)
        )
        conn.commit()
        print(f"  ✅ 清空 oauth_consumer.resource_id (consumer_id: {consumer_id})")


def main():
    print("=" * 70)
    print("通过数据库创建 Magento Integration")
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
        print("  export INTEGRATION_EMAIL=your_email@example.com")
        print("  python scripts/create_integration_via_db.py")
        sys.exit(1)
    
    print(f"数据库配置:")
    print(f"  Host: {DB_HOST}:{DB_PORT}")
    print(f"  Database: {DB_NAME}")
    print(f"  User: {DB_USER}")
    print()
    
    try:
        conn = get_db_connection()
        print("✅ 数据库连接成功")
        print()
        
        # 1. 创建 oauth_consumer
        print("1. 创建 oauth_consumer...")
        consumer_id = create_oauth_consumer(conn, INTEGRATION_NAME)
        print()
        
        # 2. 先创建 integration（临时 role_id，稍后更新）
        print("2. 创建 integration...")
        # 先创建一个临时的 role_id，稍后会更新
        temp_role_id = 0
        integration_id = create_integration(conn, INTEGRATION_NAME, INTEGRATION_EMAIL, consumer_id, temp_role_id)
        print()
        
        # 3. 创建 authorization_role（关联到 integration_id）
        print("3. 创建 authorization_role...")
        role_name = f"integration_{consumer_id}"
        role_id = create_authorization_role(conn, role_name, integration_id)
        print()
        
        # 4. 更新 integration 的 role_id
        print("4. 更新 integration 的 role_id...")
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE integration SET role_id = %s WHERE integration_id = %s",
                (role_id, integration_id)
            )
            conn.commit()
        print(f"  ✅ 已更新 integration.role_id = {role_id}")
        print()
        
        # 5. 创建 authorization_rules（权限规则）
        print("5. 创建 authorization_rules（权限规则）...")
        create_authorization_rules(conn, role_id, REQUIRED_RESOURCES)
        print()
        
        # 6. 清空 oauth_consumer.resource_id
        print("6. 清空 oauth_consumer.resource_id...")
        clear_oauth_consumer_resource_id(conn, consumer_id)
        print()
        
        # 7. 验证
        print("7. 验证创建结果...")
        integration = check_existing_integration(conn, INTEGRATION_NAME)
        if integration:
            print(f"  ✅ Integration 创建成功:")
            print(f"     integration_id: {integration['integration_id']}")
            print(f"     name: {integration['name']}")
            print(f"     status: {integration['status']} (0=未激活, 1=已激活)")
            print(f"     consumer_id: {integration['consumer_id']}")
            print(f"     role_id: {integration['role_id']}")
        print()
        
        print("=" * 70)
        print("✅ Integration 创建完成！")
        print("=" * 70)
        print()
        print("下一步:")
        print("1. 在 Magento 后台激活 Integration:")
        print(f"   System > Integrations > {INTEGRATION_NAME} > Activate")
        print()
        print("2. 清除 Magento 缓存:")
        print("   php bin/magento cache:flush")
        print()
        print("3. 获取 Access Token:")
        print("   在 Integration 编辑页面，点击 'Reset' 或 'Generate'")
        print()
        print("4. 更新 .env 文件:")
        print("   MAGENTO_API_TOKEN=新的Token")
        print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

