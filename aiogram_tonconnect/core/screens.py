from __future__ import annotations

import logging
import typing as t
import uuid
from contextlib import asynccontextmanager

from aiogram.filters.callback_data import CallbackData
from ton_connect.models import Wallet

from ..events.dispatch import TonConnectUpdate, event_name, propagate
from ..events.models import DisconnectEvent, ErrorKind, Status, TonConnectEvent
from ..view import ScreenGone
from .models import Operation, OperationKind, pack_payload

if t.TYPE_CHECKING:
    from aiogram import Bot
    from aiogram.types import Message, User

    from ..manager import TonConnectManager
    from .connector import UserConnector
    from .storage import UserStorage

logger = logging.getLogger(__name__)


class _Outgoing(t.NamedTuple):
    name: str
    event: TonConnectEvent | DisconnectEvent
    operation: Operation | None
    extra: dict[str, t.Any]


class UserScreens:
    """The screens of the operations of one user, and the events their ends send to the handlers."""

    def __init__(
        self,
        manager: TonConnectManager,
        bot: Bot,
        user: User,
        storage: UserStorage,
        connector: UserConnector,
        message: Message | None,
    ) -> None:
        self.message = message
        """The message of the current callback: new operations show their screens there."""
        self._manager = manager
        self._bot = bot
        self._user = user
        self._storage = storage
        self._connector = connector
        self._outgoing: list[_Outgoing] = []

    def new(self, kind: OperationKind, payload: str | CallbackData | None) -> Operation:
        operation = Operation(
            # 12 hex digits keep "tonconnect_wallet:<id>:<app_name>" within the 64 bytes of callback data
            id=uuid.uuid4().hex[:12],
            kind=kind,
            user=self._user,
            message=self.message,
            payload=pack_payload(payload),
        )
        logger.debug("Operation %s of %s started: %s", operation.id, self._connector.key, kind.value)
        return operation

    async def show(self, operation: Operation, screen: t.Awaitable[Message]) -> bool:
        """Show a screen of the operation; return whether it is still going, which a deleted screen ends."""
        try:
            message = await screen
        except ScreenGone:
            await self._abandon(operation)
            return False
        except Exception:
            # With no screen the user can neither finish nor leave the operation, so it is given up
            logger.debug("Operation %s of %s given up: its screen failed", operation.id, self._connector.key)
            self._connector.stop_waiting(operation)
            await self._storage.delete(operation.id)
            await self._connector.release()
            raise
        if message != operation.message:
            operation.message = message
            await self._storage.save(operation)
        return True

    async def fail(self, operation: Operation, error: Exception) -> None:
        operation.error = ErrorKind.of(error)
        if operation.error is ErrorKind.BAD_MANIFEST:
            # Only the owner of the bot can fix the manifest
            logger.warning(
                "Operation %s of %s failed, the wallet rejected the manifest: %s",
                operation.id,
                self._connector.key,
                error,
            )
        else:
            logger.debug("Operation %s of %s failed: %s", operation.id, self._connector.key, error)
        await self._storage.save(operation)
        try:
            await self.show(operation, self._manager.view.show_error(self._bot, operation))
        except Exception:
            if operation.message is None:
                raise
            # The handlers still learn how the operation ended; the user keeps the screen as it was
            logger.exception("Operation %s of %s: showing the error screen failed", operation.id, self._connector.key)
            await self.end(operation, Status.FAILED)

    async def end(self, operation: Operation, status: Status, result: t.Any = None) -> None:
        logger.debug("Operation %s of %s ended: %s", operation.id, self._connector.key, status.value)
        await self._storage.delete(operation.id)
        await self._connector.load()
        # Every operation shows a screen before it can end, and the view returns its message
        assert operation.message is not None
        event = TonConnectEvent(
            id=None if operation.kind is OperationKind.CONNECT else operation.id,
            payload=operation.payload,
            status=status,
            error=operation.error,
            message=operation.message.as_(self._bot),
        )
        extra = {"result": result, "wallet": result if isinstance(result, Wallet) else self._connector.wallet}
        self._outgoing.append(_Outgoing(event_name(operation.kind.event), event, operation, extra))

    async def leave(self, operation_id: str) -> None:
        operation = await self._storage.get(operation_id)
        if operation is None:
            return
        await self._abandon(operation)

    async def drop(self) -> None:
        """End all operations of the user, as Back does."""
        current = self.message.message_id if self.message is not None else None
        for operation in await self._storage.all():
            if operation.message is None or operation.message.message_id == current:
                # The current message is about to get a new screen, so no handler may have it
                logger.debug("Operation %s of %s dropped: a new screen replaces it", operation.id, self._connector.key)
                await self._storage.delete(operation.id)
            else:
                await self._left(operation)

    async def _abandon(self, operation: Operation) -> None:
        self._connector.stop_waiting(operation)
        if operation.kind is OperationKind.CONNECT:
            # The wallet may have approved while Back waited for the lock: that session is unchecked by ton_proof
            await self._connector.load()
            if self._connector.approved(operation):
                await self._connector.drop_session()
        await self._left(operation)
        await self._connector.release()

    async def _left(self, operation: Operation) -> None:
        # A request still waiting is cancelled, one showing an error has failed
        await self.end(operation, Status.FAILED if operation.error else Status.CANCELLED)

    def queue(self, name: str, event: DisconnectEvent, extra: dict[str, t.Any]) -> None:
        self._outgoing.append(_Outgoing(name, event, None, extra))

    @asynccontextmanager
    async def locked(self) -> t.AsyncIterator[None]:
        """Run under the lock of the user; the queued events go to the handlers after it is released."""
        # Their handlers may start the next operation. They go out after a failure too: the operations they end are
        # already deleted
        try:
            async with self._manager.lock(self._connector.key):
                # Another update or the bridge may have changed the session while this one waited
                await self._connector.load()
                yield
        finally:
            await self.flush()

    async def flush(self) -> None:
        """Send the queued events to the handlers; a screen no handler took is removed."""
        outgoing, self._outgoing = self._outgoing, []
        for item in outgoing:
            await self._deliver(item)

    async def _deliver(self, item: _Outgoing) -> None:
        name, event, operation, extra = item
        try:
            update = TonConnectUpdate(name, event)
            data = {**self._manager.workflow_data, **extra}
            handled = await propagate(self._manager.dispatcher, self._bot, self._user, update, data)
            if not handled and operation is not None:
                await self._manager.view.hide(self._bot, operation)
        except Exception:
            # The other events still go out: their operations are already deleted, so nothing would send them later
            logger.exception("Delivering %s failed for %s", name, self._connector.key)
