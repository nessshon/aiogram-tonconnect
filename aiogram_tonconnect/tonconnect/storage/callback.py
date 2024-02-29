import pickle

from .base import ATCStorageBase
from ..models import ConnectWalletCallbacks, SendTransactionCallbacks


class ConnectWalletCallbackStorage:

    def __init__(
            self,
            storage: ATCStorageBase,
            user_id: int,
            collection: str = "ConnectWalletCallbacks",
    ) -> None:
        self.storage = storage
        self.user_id = user_id
        self.collection = collection

    def _get_key(self) -> str:
        """
        Generate a unique key for the session storage.

        :return: Unique key combining the collection and user_id.
        """
        return f"{self.collection}:{self.user_id}"

    async def get(self) -> ConnectWalletCallbacks:
        value = await self.storage.get_item(self._get_key())
        return ConnectWalletCallbacks(**pickle.loads(value)) if value else None

    async def add(self, connect_wallet_callbacks: ConnectWalletCallbacks) -> None:
        serialized_value = pickle.dumps(connect_wallet_callbacks.model_dump())
        await self.storage.set_item(self._get_key(), serialized_value)

    async def remove(self) -> None:
        await self.storage.remove_item(self._get_key())


class SendTransactionCallbackStorage:

    def __init__(
            self,
            storage: ATCStorageBase,
            user_id: int,
            collection: str = "SendTransactionsCallbacks",
    ) -> None:
        self.storage = storage
        self.user_id = user_id
        self.collection = collection

    def _get_key(self) -> str:
        """
        Generate a unique key for the session storage.

        :return: Unique key combining the collection and user_id.
        """
        return f"{self.collection}:{self.user_id}"

    async def get(self) -> SendTransactionCallbacks:
        value = await self.storage.get_item(self._get_key())
        return SendTransactionCallbacks(**pickle.loads(value)) if value else None

    async def add(self, send_transaction_callbacks: SendTransactionCallbacks) -> None:
        serialized_value = pickle.dumps(send_transaction_callbacks.model_dump())
        await self.storage.set_item(self._get_key(), serialized_value)

    async def remove(self) -> None:
        await self.storage.remove_item(self._get_key())
