from typing import Optional

from pytonconnect.storage import IStorage
from redis.asyncio import Redis


class SessionStorage(IStorage):
    """
    Implementation of IStorage for session storage using Redis.

    This class provides methods to set, get, and remove items from the Redis session storage.
    """

    def __init__(
            self,
            redis: Redis,
            user_id: Optional[int] = None,
    ) -> None:
        """
        Initialize the SessionStorage.

        :param redis: Redis instance for asynchronous operations.
        :param user_id: User ID associated with the session storage.
        """
        self.redis = redis
        self.user_id = user_id

    def _get_key(self, key: str) -> str:
        """
        Generate a unique key for the session storage.

        :param key: Original key.
        :return: Unique key combining the user_id and original key.
        """
        return f"{self.user_id}{key}"

    async def set_item(self, key: str, value: str) -> None:
        """
        Set an item in the session storage.

        :param key: Key for the item.
        :param value: Value to be stored.
        """
        async with self.redis.client() as client:
            await client.set(name=self._get_key(key), value=value)

    async def get_item(self, key: str, default_value: str = None) -> str:
        """
        Get an item from the session storage.

        :param key: Key for the item.
        :param default_value: Default value if the key is not found.
        :return: Value associated with the key.
        """
        async with self.redis.client() as client:
            value = await client.get(name=self._get_key(key))
            return value.decode() if value else default_value

    async def remove_item(self, key: str) -> None:
        """
        Remove an item from the session storage.

        :param key: Key for the item to be removed.
        """
        async with self.redis.client() as client:
            await client.delete(self._get_key(key))
