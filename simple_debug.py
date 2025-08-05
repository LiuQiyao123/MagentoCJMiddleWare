#!/usr/bin/env python3
"""
简化的CJ API Token诊断脚本
"""
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
import httpx

# 从.env文件读取配置
def load_env_config():
    """从.env文件加载配置"""
    config = {}
    env_file = ".env"
    
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key] = value.strip('"\'')
    
    return config

async def check_config():
    """检查配置是否正确"""
    print("=" * 50)
    print("步骤1: 检查配置")
    print("=" * 50)
    
    try:
        config = load_env_config()
        
        # 检查CJ配置
        cj_email = config.get('CJ_API_EMAIL')
        cj_key = config.get('CJ_API_KEY')
        cj_base_url = config.get('CJ_API_BASE_URL', 'https://developers.cjdropshipping.com/api2.0/v1')
        
        print(f"CJ API Email: {cj_email}")
        print(f"CJ API Key: {cj_key[:10]}..." if cj_key else "未设置")
        print(f"CJ API Base URL: {cj_base_url}")
        
        # 检查配置完整性
        if not cj_email or not cj_key:
            print("❌ CJ配置不完整")
            return False, None
        
        print("✅ CJ配置检查通过")
        return True, {
            'email': cj_email,
            'key': cj_key,
            'base_url': cj_base_url
        }
        
    except Exception as e:
        print(f"❌ 配置检查失败: {e}")
        return False, None

async def test_token_api(config):
    """测试token获取API"""
    print("\n" + "=" * 50)
    print("步骤2: 测试Token获取API")
    print("=" * 50)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{config['base_url']}/authentication/getAccessToken",
                json={
                    "email": config['email'],
                    "password": config['key']
                },
                headers={"Content-Type": "application/json"}
            )
            
            print(f"API响应状态码: {response.status_code}")
            print(f"API响应内容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Token API调用成功")
                print(f"响应结构: {json.dumps(result, indent=2, ensure_ascii=False)}")
                return True, result
            elif response.status_code == 429:
                print("❌ API频率限制: 每5分钟只能调用1次getAccessToken")
                return False, None
            else:
                print(f"❌ API调用失败: {response.status_code}")
                return False, None
                
    except Exception as e:
        print(f"❌ Token API测试失败: {e}")
        return False, None

async def test_cache_mechanism():
    """测试缓存机制"""
    print("\n" + "=" * 50)
    print("步骤3: 测试缓存机制")
    print("=" * 50)
    
    try:
        # 检查缓存文件路径
        cache_dir = os.path.join(os.getcwd(), "cache")
        cache_file = os.path.join(cache_dir, "cj_token.json")
        
        print(f"缓存文件路径: {cache_file}")
        print(f"缓存目录: {cache_dir}")
        print(f"缓存目录存在: {os.path.exists(cache_dir)}")
        
        # 检查缓存文件是否存在
        if os.path.exists(cache_file):
            print("✅ 缓存文件存在")
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            print(f"缓存内容: {json.dumps(cache_data, indent=2, ensure_ascii=False)}")
            
            # 检查token是否过期
            if cache_data.get("expires_at"):
                expiry_dt = datetime.fromisoformat(cache_data["expires_at"])
                current_time = datetime.now(timezone.utc)
                is_valid = current_time < expiry_dt
                print(f"Token过期时间: {expiry_dt}")
                print(f"当前时间: {current_time}")
                print(f"Token是否有效: {'✅' if is_valid else '❌'}")
                return is_valid
        else:
            print("❌ 缓存文件不存在")
            return False
            
    except Exception as e:
        print(f"❌ 缓存机制测试失败: {e}")
        return False

async def test_product_api(config, token_result):
    """测试产品API调用"""
    print("\n" + "=" * 50)
    print("步骤4: 测试产品API调用")
    print("=" * 50)
    
    try:
        if not token_result or not token_result.get('result'):
            print("❌ 没有有效的token，跳过产品API测试")
            return False
        
        access_token = token_result.get('data', {}).get('accessToken')
        if not access_token:
            print("❌ 没有access token")
            return False
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 测试搜索产品
            response = await client.get(
                f"{config['base_url']}/product/list",
                params={
                    "name": "phone",
                    "current": 1,
                    "pageSize": 5
                },
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
            )
            
            print(f"产品API响应状态码: {response.status_code}")
            print(f"产品API响应内容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ 产品搜索API调用成功")
                print(f"搜索结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
                return True
            else:
                print(f"❌ 产品API调用失败: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ 产品API测试失败: {e}")
        return False

async def main():
    """主诊断流程"""
    print("CJ API Token 诊断开始")
    print(f"诊断时间: {datetime.now().isoformat()}")
    
    results = []
    
    # 步骤1: 检查配置
    config_ok, config = await check_config()
    results.append(("配置检查", config_ok))
    
    if not config_ok:
        print("\n❌ 配置检查失败，停止后续测试")
        return
    
    # 步骤2: 测试Token API
    token_api_ok, token_result = await test_token_api(config)
    results.append(("Token API测试", token_api_ok))
    
    # 步骤3: 测试缓存机制
    cache_ok = await test_cache_mechanism()
    results.append(("缓存机制测试", cache_ok))
    
    # 步骤4: 测试产品API
    if token_api_ok:
        product_api_ok = await test_product_api(config, token_result)
        results.append(("产品API测试", product_api_ok))
    else:
        results.append(("产品API测试", False))
    
    # 输出总结
    print("\n" + "=" * 50)
    print("诊断结果总结")
    print("=" * 50)
    
    for step, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{step}: {status}")
    
    # 给出建议
    print("\n" + "=" * 50)
    print("问题诊断和建议")
    print("=" * 50)
    
    if not results[0][1]:  # 配置检查失败
        print("🔧 建议: 检查.env文件中的CJ_API_EMAIL和CJ_API_KEY配置")
    elif not results[1][1]:  # Token API失败
        print("🔧 建议: CJ API可能有限流，请等待5分钟后重试")
    elif not results[2][1]:  # 缓存机制失败
        print("🔧 建议: 检查缓存目录权限，或清除缓存重新获取token")
    elif not results[3][1]:  # 产品API失败
        print("🔧 建议: 检查API权限和产品搜索参数")
    else:
        print("🎉 所有测试通过！CJ API集成正常工作")

if __name__ == "__main__":
    asyncio.run(main()) 