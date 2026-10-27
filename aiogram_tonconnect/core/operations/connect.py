from __future__ import annotations

import logging
import time
import typing as t

from ton_connect.connector import Connector
from ton_connect.exceptions import RequestTimeoutError, TonConnectError
from ton_connect.utils import find_app_wallet

from ...events.models import Status
from ..models import OperationKind
from .base import OperationsBase

if t.TYPE_CHECKING:
    from aiogram.filters.callback_data import CallbackData
    from ton_connect.models import AppWallet

    from ..models import Operation

logger = logging.getLogger(__name__)

# A QR code is scanned from another device, so the wallet has nowhere to return; tonconnect-ui does the same
QR_RETURN = "none"


class ConnectOperations(OperationsBase):
    async def connect(self, payload: str | CallbackData | None = None) -> None:
        """Ask the user to connect a wallet, disconnecting the current one; with ``ton_proof`` it proves its address."""
        async with self._screens.locked():
            await self._start_connect(payload)

    async def on_select_wallet(self, operation_id: str, app_name: str) -> None:
        """Show the connect links of the wallet chosen in the list; called by the library."""
        async with self._screens.locked():
            operation = await self._storage.get(operation_id)
            wallet = find_app_wallet(self._manager.tonconnect.app_wallets, app_name)
            if operation is not None and operation.error is None and wallet is not None:
                await self._show_connect(operation, wallet)

    async def on_wallets_page(self, operation_id: str, page: int) -> None:
        """Show a page of the wallet list; called by the library."""
        async with self._screens.locked():
            operation = await self._storage.get(operation_id)
            if operation is not None and operation.error is None:
                await self._show_connect(operation, None, page)

    async def on_connect(self, connector: Connector, error: TonConnectError | None) -> None:
        """Take the answer of the wallet to a connect; called by the library."""
        async with self._screens.locked():
            if self._connector.current() is not connector:
                # A newer connect replaced this connector; its answer belongs to no operation
                await connector.close()
                return
            operation = await self._storage.waiting_for(OperationKind.CONNECT)
            if operation is None:
                logger.debug("Connect answer of the wallet matches no operation of %s", self._connector.key)
                await connector.close()
                return
            await self._finish_connect(operation, connector, error)

    async def _start_connect(self, payload: str | CallbackData | None) -> None:
        if not self._manager.tonconnect.app_wallets:
            raise RuntimeError("The wallet catalog is empty; it loads on dispatcher startup")
        operation = self._screens.new(OperationKind.CONNECT, payload)
        await self._disconnect()
        connector = self._connector.create()
        proof = self._manager.ton_proof
        challenge = proof.challenge() if proof is not None else None
        request = connector.make_connect_request(ton_proof_payload=challenge, network=self._manager.network)
        # ton_connect caps the wait for a connection at DEFAULT_CONNECT_TIMEOUT; the deadline must not outlive it
        timeout = Connector.DEFAULT_CONNECT_TIMEOUT
        if proof is not None:
            timeout = min(proof.ttl, timeout)
        await connector.connect(request, network=self._manager.network, timeout=timeout)
        pending = await connector.storage.get_pending_connection()
        operation.session_id = pending.session_keypair.session_id
        operation.deadline = int(time.time() + timeout)
        await self._storage.save(operation)
        await self._show_connect(operation, None)

    async def _show_connect(self, operation: Operation, wallet: AppWallet | None, page: int = 0) -> None:
        connector = await self._connector.open()
        try:
            request = (await connector.storage.get_pending_connection()).connect_request
        except TonConnectError:
            # The wallet may have connected already, its answer waiting for the lock: on_connect ends the operation
            if self._connector.connection is None:
                await self._screens.fail(operation, RequestTimeoutError())
            return
        qr_link = connector.make_connect_url(request, wallet, QR_RETURN)
        open_link = None
        if wallet is not None:
            open_link = connector.make_connect_url(request, wallet, await self._connector.return_url(wallet))
        wallets = self._manager.tonconnect.app_wallets
        screen = self._manager.view.show_connect(self.bot, operation, wallets, wallet, qr_link, open_link, page)
        await self._screens.show(operation, screen)

    async def _finish_connect(self, operation: Operation, connector: Connector, error: TonConnectError | None) -> None:
        failure = error or await self._check_wallet(connector)
        if failure is not None:
            await self._connector.disconnect(connector)
            await self._screens.fail(operation, failure)
        else:
            await self._screens.end(operation, Status.DONE, connector.wallet)
        await self._connector.release()

    async def _check_wallet(self, connector: Connector) -> Exception | None:
        wallet = connector.wallet
        if wallet is None:
            return TonConnectError("The wallet connected without an account")
        proof = self._manager.ton_proof
        return await proof.check_connect(wallet) if proof is not None else None

    async def _resume_connects(self, operations: list[Operation]) -> list[Operation]:
        """Time out the connects a restart left past their deadline; return those still to resume."""
        resumed = []
        for operation in operations:
            if operation.kind is not OperationKind.CONNECT:
                continue
            if self._connector.approved(operation) or operation.deadline > time.time():
                resumed.append(operation)
            else:
                await self._screens.fail(operation, RequestTimeoutError())
        return resumed

    async def _continue_connects(self, connector: Connector, operations: list[Operation]) -> None:
        for operation in operations:
            # The wallet approved before the bot stopped: ton_connect stored the session and does not send that answer
            # again, so the connect is ended here
            if self._connector.approved(operation):
                await self._finish_connect(operation, connector, None)
            else:
                # resume_connect binds the timeout to the session the provider has now, which restore() loads
                connector.resume_connect(operation.deadline - time.time(), network=self._manager.network)
