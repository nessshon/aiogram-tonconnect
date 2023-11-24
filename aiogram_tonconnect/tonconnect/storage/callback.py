import pickle
from typing import Union

from redis.asyncio import Redis

from ..models import ConnectWalletCallbacks, SendTransactionCallbacks


class CallbackStorageBase:
    """
    Base class for callback storage.

    This class defines the common methods for handling callback storage.
    """

    def __init__(
            self,
            redis: Redis,
            user_id: int,
            collection: str,
    ) -> None:
        """
        Initialize the CallbackStorageBase.

        :param redis: Redis instance for asynchronous operations.
        :param user_id: User ID associated with the storage.
        :param collection: Collection name for storing callbacks.
        """
        self.redis = redis
        self.user_id = user_id
        self.collection = collection

    async def get(self) -> Union[ConnectWalletCallbacks, SendTransactionCallbacks]:
        """
        Get stored callbacks.

        :return: Callbacks object.
        """
        raise NotImplementedError

    async def add(self, callbacks: Union[ConnectWalletCallbacks, SendTransactionCallbacks]) -> None:
        """
        Add callbacks to the storage.

        :param callbacks: Callbacks object to be added.
        """
        raise NotImplementedError

    async def remove(self) -> None:
        """
        Remove stored callbacks.
        """
        raise NotImplementedError


class ConnectWalletCallbackStorage(CallbackStorageBase):

    def __init__(
            self,
            redis: Redis,
            user_id: int,
            collection: str = "ConnectWalletCallbacks",
    ) -> None:
        super().__init__(redis, user_id, collection)

    async def get(self) -> ConnectWalletCallbacks:
        async with self.redis.client() as client:
            serialized_value = await client.hget(self.collection, key=str(self.user_id))
            return ConnectWalletCallbacks(**pickle.loads(serialized_value)) if serialized_value else None

    async def add(self, connect_wallet_callbacks: ConnectWalletCallbacks) -> None:
        async with self.redis.client() as client:
            serialized_value = pickle.dumps(connect_wallet_callbacks.to_dict())
            await client.hset(self.collection, key=str(self.user_id), value=serialized_value)  # noqa

    async def remove(self) -> None:
        async with self.redis.client() as client:
            await client.hdel(self.collection, [str(self.user_id)])


class SendTransactionCallbackStorage(CallbackStorageBase):

    def __init__(
            self,
            redis: Redis,
            user_id: int,
            collection: str = "SendTransactionsCallbacks",
    ) -> None:
        super().__init__(redis, user_id, collection)

    async def get(self) -> SendTransactionCallbacks:
        async with self.redis.client() as client:
            serialized_value = await client.hget(self.collection, key=str(self.user_id))
            return SendTransactionCallbacks(**pickle.loads(serialized_value)) if serialized_value else None

    async def add(self, callbacks: SendTransactionCallbacks) -> None:
        async with self.redis.client() as client:
            serialized_value = pickle.dumps(callbacks.to_dict())
            await client.hset(self.collection, key=str(self.user_id), value=serialized_value)  # noqa

    async def remove(self) -> None:
        async with self.redis.client() as client:
            await client.hdel(self.collection, [str(self.user_id)])
