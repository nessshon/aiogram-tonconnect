from __future__ import annotations

import logging
import typing as t

from .core.operations.connect import ConnectOperations
from .core.operations.disconnect import DisconnectOperations
from .core.operations.request import RequestOperations

if t.TYPE_CHECKING:
    from ton_connect.models import AppWallet, Wallet


logger = logging.getLogger(__name__)


class TonConnectContext(ConnectOperations, RequestOperations, DisconnectOperations):
    """TON Connect of one user, given to handlers as ``tc``.

    An operation shows its screen in the message of the callback, or a new one, and ends with an event of
    ``TonConnectRouter`` carrying its ``payload``. While it runs, that message is the library's: call ``cancel``
    before showing something else in it or taking the user elsewhere.
    """

    @property
    def wallet(self) -> Wallet | None:
        """The connected wallet, or ``None``."""
        return self._connector.wallet

    @property
    def app_wallet(self) -> AppWallet | None:
        """The catalog entry of the connected wallet, or ``None``."""
        return self._connector.app_wallet

    async def load(self) -> TonConnectContext:
        """Read the stored session of the user."""
        await self._connector.load()
        return self

    async def resume(self) -> None:
        """Wait again for the operations a restart left pending; called by the library on startup."""
        async with self._screens.locked():
            operations = await self._storage.waiting()
            if not operations:
                return
            logger.debug("Resuming %d operations of %s", len(operations), self._connector.key)
            connector = self._connector.create()
            # The answers to requests need their futures before the stream resumes, connects need its session
            requests = await self._resume_requests(connector, operations)
            connects = await self._resume_connects(operations)
            if not (requests or connects):
                await connector.close()
                return
            restored = await connector.restore()
            await self._continue_connects(connector, connects)
            if not restored:
                await self._lose_requests(connector, requests)
            await self._connector.release()
