"""Direct test of the rewritten cloud providers."""
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from opsyield.providers.gcp import GCPProvider
from opsyield.providers.aws import AWSProvider
from opsyield.providers.azure import AzureProvider


async def main():
    for name, cls in [("GCP", GCPProvider), ("AWS", AWSProvider), ("Azure", AzureProvider)]:
        print(f"\n{'='*60}")
        print(f"  {name} Provider")
        print(f"{'='*60}")
        try:
            provider = cls()
            status = await provider.get_status()
            print(json.dumps(status, indent=2, default=str))
        except Exception as e:
            print(f"  EXCEPTION: {e}")

asyncio.run(main())
