import os
import httpx
import asyncio
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("magento_debug")

async def debug_magento_auth():
    """
    Debug script to test Magento API authentication independently.
    Reads credentials from environment variables.
    """
    base_url = os.getenv("MAGENTO_BASE_URL")
    token = os.getenv("MAGENTO_API_TOKEN")

    if not base_url or not token:
        logger.error("Missing environment variables: MAGENTO_BASE_URL or MAGENTO_API_TOKEN")
        return

    url = f"{base_url}/rest/V1/store/storeConfigs"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    masked_token = f"{token[:5]}...{token[-5:]}" if len(token) > 10 else "***"
    logger.info(f"Debugging Magento Auth...")
    logger.info(f"URL: {url}")
    logger.info(f"Token: {masked_token}")
    
    try:
        # Increased timeout and verify=False
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            logger.info("Sending GET request...")
            response = await client.get(url, headers=headers)
            
            logger.info(f"Response Status Code: {response.status_code}")
            logger.info(f"Response Headers: {dict(response.headers)}")
            logger.info(f"Response Body: {response.text[:500]}...") # Print first 500 chars

            if response.status_code == 200:
                logger.info("✅ Authentication Successful!")
            elif response.status_code == 401:
                logger.error("❌ Authentication Failed: 401 Unauthorized. Check your Token.")
            else:
                logger.warning(f"⚠️ Unexpected Status Code: {response.status_code}")

    except Exception as e:
        logger.error(f"❌ Request Failed: {repr(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_magento_auth())
