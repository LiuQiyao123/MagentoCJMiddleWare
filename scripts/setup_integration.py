#!/usr/bin/env python3
"""
一键设置 Magento Integration
整合创建、激活、生成 Token 和验证的完整流程
"""
import os
import sys
import subprocess
import argparse

# 脚本目录
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPTS_DIR)


def run_script(script_name: str, description: str) -> bool:
    """运行脚本并返回是否成功"""
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    
    if not os.path.exists(script_path):
        print(f"❌ 脚本不存在: {script_path}")
        return False
    
    print()
    print("=" * 70)
    print(f"步骤: {description}")
    print("=" * 70)
    print()
    
    try:
        # 使用 subprocess 运行脚本，继承环境变量
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=PROJECT_ROOT,
            env=os.environ.copy(),
            check=False
        )
        
        if result.returncode == 0:
            print(f"✅ {description} 完成")
            return True
        else:
            print(f"❌ {description} 失败 (退出码: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"❌ 运行脚本时出错: {e}")
        return False


def check_environment():
    """检查必要的环境变量"""
    required_vars = [
        'MAGENTO_DB_HOST',
        'MAGENTO_DB_PORT',
        'MAGENTO_DB_NAME',
        'MAGENTO_DB_USER',
        'MAGENTO_DB_PASSWORD',
        'MAGENTO_BASE_URL'
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print("❌ 缺少必要的环境变量:")
        for var in missing:
            print(f"   - {var}")
        print()
        print("请设置这些环境变量或确保 .env 文件已正确加载")
        return False
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description='一键设置 Magento Integration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 完整设置流程
  python scripts/setup_integration.py

  # 跳过创建，只激活和生成 Token
  python scripts/setup_integration.py --skip-create

  # 只验证现有配置
  python scripts/setup_integration.py --verify-only
        """
    )
    
    parser.add_argument(
        '--skip-create',
        action='store_true',
        help='跳过创建 Integration（假设已存在）'
    )
    
    parser.add_argument(
        '--skip-activate',
        action='store_true',
        help='跳过激活 Integration'
    )
    
    parser.add_argument(
        '--skip-token',
        action='store_true',
        help='跳过生成 Token'
    )
    
    parser.add_argument(
        '--skip-verify',
        action='store_true',
        help='跳过验证步骤'
    )
    
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='只运行验证步骤'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("Magento Integration 一键设置")
    print("=" * 70)
    print()
    
    # 检查环境变量
    if not check_environment():
        sys.exit(1)
    
    # 如果只是验证
    if args.verify_only:
        success = run_script('verify_integration.py', '验证 Integration 配置')
        sys.exit(0 if success else 1)
    
    # 执行完整流程
    steps = []
    
    if not args.skip_create:
        steps.append(('create_integration_via_db.py', '创建 Integration'))
    
    if not args.skip_activate:
        steps.append(('activate_integration.py', '激活 Integration'))
    
    if not args.skip_token:
        steps.append(('generate_access_token.py', '生成 Access Token'))
    
    if not args.skip_verify:
        steps.append(('verify_integration.py', '验证 Integration 配置'))
    
    if not steps:
        print("⚠️  所有步骤都被跳过，没有要执行的操作")
        sys.exit(0)
    
    print(f"将执行 {len(steps)} 个步骤:")
    for i, (script, desc) in enumerate(steps, 1):
        print(f"  {i}. {desc}")
    print()
    
    # 询问确认
    try:
        response = input("是否继续? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("已取消")
            sys.exit(0)
    except KeyboardInterrupt:
        print("\n已取消")
        sys.exit(0)
    
    # 执行步骤
    failed_steps = []
    for script, description in steps:
        if not run_script(script, description):
            failed_steps.append(description)
            # 询问是否继续
            try:
                response = input("\n步骤失败，是否继续执行后续步骤? (y/N): ").strip().lower()
                if response not in ['y', 'yes']:
                    break
            except KeyboardInterrupt:
                print("\n已中断")
                break
    
    # 总结
    print()
    print("=" * 70)
    if not failed_steps:
        print("✅ 所有步骤执行成功！")
        print("=" * 70)
        print()
        print("下一步:")
        print("1. 更新 .env 文件中的 MAGENTO_API_TOKEN")
        print("2. 重启应用程序以使用新的 Token")
        print("3. 测试产品同步功能")
        sys.exit(0)
    else:
        print("⚠️  以下步骤失败:")
        for step in failed_steps:
            print(f"   - {step}")
        print("=" * 70)
        print()
        print("请检查错误信息并手动修复后重试")
        sys.exit(1)


if __name__ == '__main__':
    main()


