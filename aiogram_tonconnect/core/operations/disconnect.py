from __future__ import annotations

import logging
import typing as t

from ton_connect import Event
from ton_connect.exceptions import TonConnectError, UnknownAppError, WalletNotConnectedError

from ...events.dispatch import event_name
from ...events.models import DisconnectEvent
from ..models import pack_payload
from .base import OperationsBase

if t.TYPE_CHECKING:
    from aiogram.filters.callback_data import CallbackData
    from ton_connect.connector import Connector

logger = logging.getLogger(__name__)


class DisconnectOperations(OperationsBase):
    async def disconnect(self, payload: str | CallbackData | None = None) -> None:
        """Disconnect the wallet and drop the operations; ``disconnect`` handlers get ``payload``.

        Outside an update there is no message, so no event is sent.
        """
        message = self._screens.message or self._user_message
        async with self._screens.locked():
            wallet = self._connector.wallet
            await self._disconnect()
            if message is not None:
                event = DisconnectEvent(payload=pack_payload(payload), message=message.as_(self.bot))
                self._screens.queue(event_name(Event.DISCONNECT), event, {"wallet": wallet})

    async def on_disconnect(self, connector: Connector, error: TonConnectError | None) -> None:
        """Take a disconnect made in the wallet; called by the library."""
        # ton_connect drops the session on UNKNOWN_APP too: the wallet does not know it anymore
        if error is not None and not isinstance(error, UnknownAppError):
            logger.warning("Disconnect in the wallet failed for %s: %s", self._connector.key, error)
            return
        async with self._screens.locked():
            for operation in await self._storage.waiting():
                await self._screens.fail(operation, WalletNotConnectedError())
            await self._connector.forget(connector)
