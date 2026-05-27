import os
import requests
import sys

# Read from env
BASE_URL = os.getenv("MAGENTO_BASE_URL", "https://shop.yokileopard.top")
TOKEN = os.getenv("MAGENTO_API_TOKEN") # Use direct var name from .env if injected, or fallback

if not TOKEN:
    # Fallback to what I know from .env file read earlier
    TOKEN = "eyJraWQiOiIxIiwiYWxnIjoiSFMyNTYifQ.eyJ1aWQiOjIsInV0eXBpZCI6MiwiaWF0IjoxNzU0OTY3NzM5LCJleHAiOjE3NTQ5NzEzMzl9.0d-hJpbOlYTLVRo_NBTlN26vSN0EzSioEk7-qmdWIKM"

print(f"Testing Magento API at: {BASE_URL}")
print(f"Token starts with: {TOKEN[:10]}...")

url = f"{BASE_URL}/rest/V1/store/storeConfigs"
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

try:
    response = requests.get(url, headers=headers, timeout=15)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Body Preview: {response.text[:200]}")
    
    if response.status_code == 200:
        print("SUCCESS: Magento API connection valid.")
        sys.exit(0)
    elif response.status_code == 401:
        print("FAILURE: Unauthorized. Token is invalid or expired.")
        sys.exit(1)
    elif response.status_code == 404:
        print("FAILURE: Endpoint not found. Check URL structure.")
        sys.exit(1)
    else:
        print(f"FAILURE: Unexpected status {response.status_code}")
        sys.exit(1)

except Exception as e:
    print(f"ERROR: Connection failed - {e}")
    sys.exit(1)

