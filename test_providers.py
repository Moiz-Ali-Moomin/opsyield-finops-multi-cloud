import asyncio
import logging
import sys
import os

# Ensure user site-packages is in path
user_site = os.path.expanduser("~\\AppData\\Roaming\\Python\\Python313\\site-packages")
if user_site not in sys.path:
    sys.path.append(user_site)

from opsyield.providers.gcp import GCPProvider
from opsyield.providers.aws import AWSProvider
from opsyield.providers.azure import AzureProvider

logging.basicConfig(level=logging.INFO)

async def test_providers():
    print("\n--- Testing GCP Provider ---")
    try:
        gcp = GCPProvider()
        status = await gcp.get_status()
        print(f"GCP Status: {status}")
    except Exception as e:
        print(f"GCP Init Failed: {e}")

    print("\n--- Testing AWS Provider ---")
    try:
        aws = AWSProvider()
        status = await aws.get_status()
        print(f"AWS Status: {status}")
    except Exception as e:
        print(f"AWS Init Failed: {e}")

    print("\n--- Testing Azure Provider ---")
    try:
        azure = AzureProvider()
        status = await azure.get_status()
        print(f"Azure Status: {status}")
    except Exception as e:
        print(f"Azure Init Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_providers())
