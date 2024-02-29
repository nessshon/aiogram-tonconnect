from aiogram_tonconnect.tonconnect.storage.base import ATCStorageBase


class SessionStorage:
    KEY_LAST_EVENT_ID = 'last_event_id'
    KEY_CONNECTION = 'connection'

    def __init__(self, storage: ATCStorageBase, user_id: int) -> None:
        """
        Initialize the SessionStorage.

        :param storage: Storage for storing session data.
        :param user_id: User ID associated with the session storage.
        """
        self.storage = storage
        self.user_id = user_id

    def _get_key(self, key: str) -> str:
        """
        Generate a unique key for the session storage.

        :param key: Original key.
        :return: Unique key combining the user_id and original key.
        """
        return f"{self.user_id}:{key}"

    async def set_item(self, key: str, value: str) -> None:
        await self.storage.set_item(self._get_key(key), value)

    async def get_item(self, key: str, default_value: str = None) -> str:
        value = await self.storage.get_item(self._get_key(key), default_value)
        return value.decode() if isinstance(value, bytes) else value

    async def remove_item(self, key: str) -> None:
        await self.storage.remove_item(self._get_key(key))
