from abc import ABCMeta
from typing import Any

from redis.asyncio import Redis


class ATCStorageBase(metaclass=ABCMeta):
    """
    Base class for all storage classes.
    """

    async def get_item(self, key: Any, default_value: str = None) -> Any:
        """
        Get an item from the storage.

        :param key: Key for the item.
        :param default_value: Default value if the item is not found.
        :return: Value of the item.
        """
        raise NotImplementedError

    async def set_item(self, key: Any, value: Any) -> None:
        """
        Set an item in the storage.

        :param key: Key for the item.
        :param value: Value of the item.
        """
        raise NotImplementedError

    async def remove_item(self, key: Any) -> None:
        """
        Remove an item from the storage.

        :param key: Key for the item to be removed.
        """
        raise NotImplementedError


class ATCRedisStorage(ATCStorageBase):

    def __init__(self, redis: Redis) -> None:
        """
        :param redis: Redis instance for asynchronous operations.
        """
        self.redis = redis

    async def set_item(self, key: Any, value: Any) -> None:
        async with self.redis.client() as client:
            await client.set(name=key, value=value)

    async def get_item(self, key: Any, default_value: str = None) -> Any:
        async with self.redis.client() as client:
            value = await client.get(name=key)
            return value if value else default_value

    async def remove_item(self, key: Any) -> None:
        async with self.redis.client() as client:
            await client.delete(key)


class ATCMemoryStorage(ATCStorageBase):
    data = {}

    async def set_item(self, key: Any, value: Any) -> None:
        self.data[key] = value

    async def get_item(self, key: Any, default_value: str = None) -> Any:
        return self.data.get(key) if key in self.data else default_value

    async def remove_item(self, key: Any) -> None:
        self.data.pop(key, None)
