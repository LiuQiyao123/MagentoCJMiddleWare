#!/usr/bin/env python3
"""
激活 Magento Integration
通过数据库直接激活 Integration，并清除缓存
"""
import os
import sys
import pymysql
from typing import Optional, Dict

# 从环境变量获取配置
DB_HOST = os.getenv('MAGENTO_DB_HOST', 'localhost')
DB_PORT = int(os.getenv('MAGENTO_DB_PORT', 3306))
DB_NAME = os.getenv('MAGENTO_DB_NAME', 'magento')
DB_USER = os.getenv('MAGENTO_DB_USER', 'root')
DB_PASSWORD = os.getenv('MAGENTO_DB_PASSWORD', '')

INTEGRATION_NAME = os.getenv('INTEGRATION_NAME', 'CJ_Sync')
MAGENTO_PATH = os.getenv('MAGENTO_PATH', '/var/www/html')  # Magento 安装路径


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


def check_integration(conn, name: str) -> Optional[Dict]:
    """检查 Integration 是否存在"""
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT integration_id, name, status, consumer_id, role_id FROM integration WHERE name = %s",
            (name,)
        )
        result = cursor.fetchone()
        return result


def activate_integration(conn, name: str) -> bool:
    """激活 Integration"""
    with conn.cursor() as cursor:
        # 检查 Integration 是否存在
        integration = check_integration(conn, name)
        if not integration:
            print(f"❌ Integration '{name}' 不存在")
            return False
        
        if integration['status'] == 1:
            print(f"✅ Integration '{name}' 已经激活")
            return True
        
        # 激活 Integration (status = 1)
        cursor.execute(
            "UPDATE integration SET status = 1, updated_at = NOW() WHERE name = %s",
            (name,)
        )
        conn.commit()
        print(f"✅ Integration '{name}' 已激活 (integration_id: {integration['integration_id']})")
        return True


def clear_magento_cache(magento_path: str) -> bool:
    """清除 Magento 缓存"""
    import subprocess
    
    if not os.path.exists(magento_path):
        print(f"⚠️  Magento 路径不存在: {magento_path}")
        print("   请手动清除缓存: php bin/magento cache:flush")
        return False
    
    cache_script = os.path.join(magento_path, 'bin', 'magento')
    if not os.path.exists(cache_script):
        print(f"⚠️  Magento CLI 脚本不存在: {cache_script}")
        print("   请手动清除缓存: php bin/magento cache:flush")
        return False
    
    try:
        # 执行缓存清除命令
        result = subprocess.run(
            ['php', cache_script, 'cache:flush'],
            cwd=magento_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ Magento 缓存已清除")
            return True
        else:
            print(f"⚠️  清除缓存时出现警告: {result.stderr}")
            print("   请手动清除缓存: php bin/magento cache:flush")
            return False
    except subprocess.TimeoutExpired:
        print("⚠️  清除缓存超时")
        print("   请手动清除缓存: php bin/magento cache:flush")
        return False
    except Exception as e:
        print(f"⚠️  无法自动清除缓存: {e}")
        print("   请手动清除缓存: php bin/magento cache:flush")
        return False


def main():
    print("=" * 70)
    print("激活 Magento Integration")
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
        print("  export MAGENTO_PATH=/var/www/html  # 可选")
        print("  python scripts/activate_integration.py")
        sys.exit(1)
    
    print(f"配置:")
    print(f"  Integration Name: {INTEGRATION_NAME}")
    print(f"  Database: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    print(f"  Magento Path: {MAGENTO_PATH}")
    print()
    
    try:
        conn = get_db_connection()
        print("✅ 数据库连接成功")
        print()
        
        # 1. 检查 Integration
        print("1. 检查 Integration...")
        integration = check_integration(conn, INTEGRATION_NAME)
        if not integration:
            print(f"❌ Integration '{INTEGRATION_NAME}' 不存在")
            print("   请先运行 scripts/create_integration_via_db.py 创建 Integration")
            sys.exit(1)
        
        print(f"   integration_id: {integration['integration_id']}")
        print(f"   status: {integration['status']} (0=未激活, 1=已激活)")
        print(f"   consumer_id: {integration['consumer_id']}")
        print(f"   role_id: {integration['role_id']}")
        print()
        
        # 2. 激活 Integration
        print("2. 激活 Integration...")
        if not activate_integration(conn, INTEGRATION_NAME):
            sys.exit(1)
        print()
        
        # 3. 清除缓存
        print("3. 清除 Magento 缓存...")
        clear_magento_cache(MAGENTO_PATH)
        print()
        
        # 4. 验证
        print("4. 验证激活状态...")
        integration = check_integration(conn, INTEGRATION_NAME)
        if integration and integration['status'] == 1:
            print(f"   ✅ Integration 已成功激活")
        else:
            print(f"   ❌ Integration 激活失败")
            sys.exit(1)
        print()
        
        print("=" * 70)
        print("✅ Integration 激活完成！")
        print("=" * 70)
        print()
        print("下一步:")
        print("1. 获取 Access Token:")
        print("   运行: python scripts/generate_access_token.py")
        print()
        print("2. 或者手动在 Magento 后台获取 Token:")
        print(f"   System > Integrations > {INTEGRATION_NAME} > Reset Token")
        print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()


