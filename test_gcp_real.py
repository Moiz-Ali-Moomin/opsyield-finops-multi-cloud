import asyncio
import logging
from opsyield.providers.gcp import GCPProvider

logging.basicConfig(level=logging.INFO)

async def test_gcp():
    print("Initializing GCP Provider...")
    try:
        provider = GCPProvider()
        print("Provider initialized.")
        
        print("Checking status...")
        status = await provider.get_status()
        print(f"Status: {status}")
        
    except Exception as e:
        print(f"Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_gcp())
