import redis.asyncio as aioredis

from src.config import settings


redis: aioredis.Redis = aioredis.from_url(
    url=settings.cache.url,
    max_connections=settings.cache.max_connections,
)
