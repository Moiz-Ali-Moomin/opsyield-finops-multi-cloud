import json
import logging
import os
from typing import Any, Optional, Dict
import aioredis

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600")) # Default 1 hour TTL

class RedisCache:
    _pool: Optional[aioredis.Redis] = None

    @classmethod
    async def get_client(cls) -> aioredis.Redis:
        if cls._pool is None:
            cls._pool = aioredis.from_url(REDIS_URL, decode_responses=True)
            logger.info(f"Initialized Redis connection to {REDIS_URL}")
        return cls._pool

    @classmethod
    async def get(cls, key: str) -> Optional[Any]:
        client = await cls.get_client()
        try:
            data = await client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None

    @classmethod
    async def set(cls, key: str, value: Any, ttl: int = CACHE_TTL) -> bool:
        client = await cls.get_client()
        try:
            serialized = json.dumps(value)
            await client.set(key, serialized, ex=ttl)
            return True
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False

    @classmethod
    async def invalidate(cls, key: str) -> bool:
        client = await cls.get_client()
        try:
            await client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis invalidate error for key {key}: {e}")
            return False

    @classmethod
    async def cache_wrapper(cls, key: str, func, *args, ttl: int = CACHE_TTL, **kwargs):
        """
        Wrapper to fetch from cache if exists, otherwise compute, cache, and return.
        """
        cached = await cls.get(key)
        if cached is not None:
            logger.debug(f"Cache hit: {key}")
            return cached
            
        logger.debug(f"Cache miss: {key}. Computing...")
        result = await func(*args, **kwargs)
        if result is not None:
            await cls.set(key, result, ttl=ttl)
        return result
