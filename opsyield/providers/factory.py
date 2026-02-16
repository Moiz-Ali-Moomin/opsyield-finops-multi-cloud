"""
ProviderFactory — Concurrent cloud status with timeout guards.

Architecture:
  1. Instantiate all providers
  2. Fire all get_status() in parallel via asyncio.gather()
  3. Each provider internally uses asyncio.to_thread(subprocess.run)
  4. Outer safe_status() adds a 20s hard timeout per provider
  5. 60s TTL in-memory cache prevents repeated CLI calls
"""
import asyncio
import time
import logging
import os
from typing import Dict, Type, Any

from .base import CloudProvider
from .gcp import GCPProvider
from .aws import AWSProvider
from .azure import AzureProvider

logger = logging.getLogger("opsyield-factory")

# ─── In-memory status cache (TTL = 60s) ───
_status_cache: Dict[str, Any] = {}
_cache_timestamp: float = 0.0
_CACHE_TTL: float = 60.0


async def safe_status(name: str, provider_instance, timeout: float = 20.0) -> Dict[str, Any]:
    """
    Run a provider's get_status() with a hard timeout guard.

    Guarantees:
      - Returns in ≤ timeout seconds
      - Never raises
      - Returns structured error on timeout/exception
    """
    try:
        result = await asyncio.wait_for(
            provider_instance.get_status(),
            timeout=timeout,
        )
        return result
    except asyncio.TimeoutError:
        logger.warning(f"Provider '{name}' timed out after {timeout}s")
        return {
            "installed": True,
            "authenticated": False,
            "error": f"Status check timed out after {timeout}s",
            "debug": {"timeout": True},
        }
    except Exception as e:
        logger.error(f"Provider '{name}' failed: {e}")
        return {
            "installed": False,
            "authenticated": False,
            "error": str(e),
            "debug": {"exception": str(e)},
        }


def _get_env_snapshot() -> dict:
    """Capture environment variables relevant to cloud auth debugging."""
    return {
        "USERPROFILE": os.environ.get("USERPROFILE", "(not set)"),
        "HOME": os.environ.get("HOME", "(not set)"),
        "AWS_PROFILE": os.environ.get("AWS_PROFILE", "(not set)"),
        "AZURE_CONFIG_DIR": os.environ.get("AZURE_CONFIG_DIR", "(not set)"),
        "CLOUDSDK_CONFIG": os.environ.get("CLOUDSDK_CONFIG", "(not set)"),
        "PATH_len": len(os.environ.get("PATH", "")),
        "PAGER": os.environ.get("PAGER", "(not set)"),
        "in_docker": os.path.exists("/.dockerenv"),
    }


class ProviderFactory:
    _providers: Dict[str, Type] = {
        'gcp': GCPProvider,
        'aws': AWSProvider,
        'azure': AzureProvider,
    }

    @classmethod
    def get_provider(cls, provider_name: str):
        provider_class = cls._providers.get(provider_name.lower())
        if not provider_class:
            raise ValueError(f"Unknown provider: {provider_name}")
        return provider_class()

    @classmethod
    async def get_all_statuses(cls) -> Dict[str, Any]:
        """
        Concurrent status check with TTL cache.

        Returns {gcp: {...}, aws: {...}, azure: {...}, _meta: {...}}
        """
        global _status_cache, _cache_timestamp

        # ─── Cache hit ───
        now = time.monotonic()
        if _status_cache and (now - _cache_timestamp) < _CACHE_TTL:
            logger.info("Returning cached cloud status")
            return _status_cache

        # ─── Docker warning ───
        if os.path.exists("/.dockerenv"):
            logger.warning("Running inside Docker — host credentials may not be mounted")

        # ─── Parallel execution ───
        t0 = time.monotonic()
        provider_names = list(cls._providers.keys())
        instances = []
        for name in provider_names:
            try:
                instances.append(cls._providers[name]())
            except Exception as e:
                logger.error(f"Failed to instantiate '{name}': {e}")
                instances.append(None)

        tasks = []
        for name, inst in zip(provider_names, instances):
            if inst is not None:
                tasks.append(safe_status(name, inst, timeout=20.0))
            else:
                async def _fail(n=name):
                    return {
                        "installed": False,
                        "authenticated": False,
                        "error": f"Failed to instantiate {n}",
                    }
                tasks.append(_fail())

        results = await asyncio.gather(*tasks, return_exceptions=False)
        elapsed = time.monotonic() - t0

        # ─── Build response ───
        statuses: Dict[str, Any] = {}
        for name, result in zip(provider_names, results):
            statuses[name] = result

        statuses["_meta"] = {
            "elapsed_ms": round(elapsed * 1000),
            "env": _get_env_snapshot(),
        }

        # ─── Update cache ───
        _status_cache = statuses
        _cache_timestamp = time.monotonic()

        logger.info(f"Cloud status checked in {elapsed:.2f}s: {[n for n in provider_names]}")
        return statuses
