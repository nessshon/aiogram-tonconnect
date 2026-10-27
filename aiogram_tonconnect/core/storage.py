import asyncio
import typing as t
from contextlib import asynccontextmanager
from weakref import WeakValueDictionary

from aiogram.fsm.storage.base import BaseStorage, StorageKey
from ton_connect import ProviderStorage
from ton_connect.exceptions import TonConnectError
from ton_connect.models import ActiveConnection

from .models import Operation, OperationKind

_SESSION_PREFIX = f"{ProviderStorage.KEY_PREFIX}::"


def session_key(bot_id: int, user_id: int) -> str:
    return f"{bot_id}:{user_id}"


def _record(bot_id: int, user_id: int) -> StorageKey:
    # A bot has no private chat with itself: chat_id=bot_id never meets the FSM record of a user
    # (chat_id=user_id) or of another bot sharing the storage, whatever the key builder
    return StorageKey(bot_id=bot_id, chat_id=bot_id, user_id=user_id)


def _session_record(key: str) -> StorageKey:
    # Another key would be stored as the session and overwrite it
    if not key.startswith(_SESSION_PREFIX):
        raise ValueError(f"Unexpected ton_connect storage key: {key!r}")
    bot_id, _, user_id = key.removeprefix(_SESSION_PREFIX).partition(":")
    return _record(int(bot_id), int(user_id))


class KeyedLock:
    """An ``asyncio.Lock`` per key, dropped once nobody holds it."""

    def __init__(self) -> None:
        self._locks: WeakValueDictionary[t.Hashable, asyncio.Lock] = WeakValueDictionary()

    def __call__(self, key: t.Hashable) -> asyncio.Lock:
        lock = self._locks.get(key)
        if lock is None:
            lock = self._locks[key] = asyncio.Lock()
        return lock


class Storage:
    """``ton_connect`` sessions and user operations in the aiogram FSM storage.

    A user record holds both and is updated under a lock: the bridge rewrites the session on every event.
    """

    def __init__(self, storage: BaseStorage) -> None:
        self._storage = storage
        self._lock = KeyedLock()

    async def set_item(self, key: str, value: t.Any) -> None:
        async with _updated(self._storage, self._lock, _session_record(key)) as data:
            data["session"] = value

    async def get_item(self, key: str) -> t.Any | None:
        return (await self._storage.get_data(_session_record(key))).get("session")

    async def remove_item(self, key: str) -> None:
        async with _updated(self._storage, self._lock, _session_record(key)) as data:
            data.pop("session", None)

    def user(self, bot_id: int, user_id: int) -> "UserStorage":
        return UserStorage(self, bot_id, user_id)

    async def users(self, bot_id: int) -> list[int]:
        """Return the users with operations, to resume on startup."""
        return list((await self._storage.get_data(_record(bot_id, bot_id))).get("users", []))


class UserStorage:
    """The session and the operations of one user."""

    def __init__(self, storage: Storage, bot_id: int, user_id: int) -> None:
        self._storage = storage._storage
        self._lock = storage._lock
        self._bot_id = bot_id
        self._user_id = user_id
        self._record = _record(bot_id, user_id)
        self.key = session_key(bot_id, user_id)
        """The key of the user in ``ton_connect``: of the session and of the connector."""
        self._session = ProviderStorage(storage, self.key)

    async def connection(self) -> ActiveConnection | None:
        try:
            connection = await self._session.get_connection()
        except TonConnectError:
            # Nothing stored; an unreadable session is dropped and logged by ton_connect
            return None
        return connection if isinstance(connection, ActiveConnection) else None

    async def all(self) -> list[Operation]:
        data = await self._storage.get_data(self._record)
        return [Operation.model_validate(raw) for raw in data.get("operations", {}).values()]

    async def waiting(self) -> list[Operation]:
        """Return the operations still waiting for the wallet: those without an error."""
        return [op for op in await self.all() if op.error is None]

    async def get(self, operation_id: str) -> Operation | None:
        return next((op for op in await self.all() if op.id == operation_id), None)

    async def waiting_for(self, kind: OperationKind) -> Operation | None:
        return next((op for op in await self.waiting() if op.kind is kind), None)

    async def answered_by(self, session_id: str | None, request_id: int) -> Operation | None:
        """Return the waiting operation a wallet answer is for."""
        return next(
            (op for op in await self.waiting() if (op.session_id, op.request_id) == (session_id, request_id)), None
        )

    async def same_request(self, kind: OperationKind, payload: str | None) -> Operation | None:
        """Return the waiting request a repeated call would duplicate."""
        return next((op for op in await self.waiting() if (op.kind, op.payload) == (kind, payload)), None)

    async def forget_session(self) -> None:
        """Remove the stored session, a pending connect included."""
        await self._session.remove_connection()

    async def save(self, operation: Operation) -> None:
        # Indexed first: a stop in between leaves an indexed user with nothing to resume, not an operation never resumed
        await self._index(add=True)
        async with _updated(self._storage, self._lock, self._record) as data:
            data["operations"][operation.id] = operation.model_dump(mode="json")

    async def delete(self, *operation_ids: str) -> None:
        async with _updated(self._storage, self._lock, self._record) as data:
            had = bool(data["operations"])
            for operation_id in operation_ids:
                data["operations"].pop(operation_id, None)
            emptied = had and not data["operations"]
        if emptied:
            await self._index(add=False)

    async def _index(self, *, add: bool) -> None:
        record = _record(self._bot_id, self._bot_id)
        async with self._lock(record):
            known = set((await self._storage.get_data(record)).get("users", []))
            users = known | {self._user_id} if add else known - {self._user_id}
            if users != known:
                await self._storage.set_data(record, {"users": sorted(users)} if users else {})


@asynccontextmanager
async def _updated(storage: BaseStorage, lock: KeyedLock, record: StorageKey) -> t.AsyncIterator[dict[str, t.Any]]:
    # The lock is per process: bot processes sharing a storage may lose each other's updates
    async with lock(record):
        data = await storage.get_data(record)
        data = {**data, "operations": dict(data.get("operations", {}))}
        yield data
        await storage.set_data(record, {key: value for key, value in data.items() if value})
