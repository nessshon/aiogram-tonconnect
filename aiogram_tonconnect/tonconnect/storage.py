import asyncio
from typing import Any, Optional

from redis.asyncio import Redis
from tonutils.tonconnect import IStorage


class ATCRedisStorage(IStorage):

    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def set_item(self, key: str, value: str) -> None:
        async with self.redis.client() as client:
            await client.set(name=key, value=value)

    async def get_item(self, key: str, default_value: Optional[str] = None) -> Optional[str]:
        async with self.redis.client() as client:
            value = await client.get(name=key)
            return value if value else default_value

    async def remove_item(self, key: str) -> None:
        async with self.redis.client() as client:
            await client.delete(key)


class ATCMemoryStorage(IStorage):
    data: dict[str, Any] = {}

    def __init__(self) -> None:
        self.lock = asyncio.Lock()

    async def set_item(self, key: str, value: str) -> None:
        async with self.lock:
            self.data[key] = value

    async def get_item(self, key: str, default_value: Optional[str] = None) -> Optional[str]:
        async with self.lock:
            return self.data.get(key) if key in self.data else default_value

    async def remove_item(self, key: str) -> None:
        async with self.lock:
            self.data.pop(key, None)
