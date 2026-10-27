from __future__ import annotations

import logging
import time
import typing as t

from ton_connect.connector import Connector
from ton_connect.exceptions import TonConnectError, WalletNotConnectedError
from ton_connect.models import SendTransactionPayload, SignDataResult

from ...events.models import Status
from ..models import OperationKind, pack_payload
from .base import OperationsBase

if t.TYPE_CHECKING:
    from aiogram.filters.callback_data import CallbackData
    from ton_connect.models import SendTransactionResult, SignDataPayload, SignMessageResult

    from ..models import Operation

logger = logging.getLogger(__name__)

# How long a request past its deadline still waits after a restart: the bridge sends what it keeps for us as soon as
# the stream opens, and an answer given while the bot was down may be there
RESUME_WINDOW = 10


class RequestOperations(OperationsBase):
    async def send_transaction(
        self, transaction: SendTransactionPayload, payload: str | CallbackData | None = None
    ) -> str:
        """Ask the connected wallet to send a transaction.

        :return: Operation ID; a repeat with the same ``payload`` while the request waits returns it and sends nothing.
        """
        async with self._screens.locked():
            return await self._request(OperationKind.TRANSACTION, transaction, payload)

    async def sign_message(self, transaction: SendTransactionPayload, payload: str | CallbackData | None = None) -> str:
        """Ask the connected wallet to sign a transaction for a relayer to send (gasless).

        :return: Operation ID, as in ``send_transaction``.
        """
        async with self._screens.locked():
            return await self._request(OperationKind.SIGN_MESSAGE, transaction, payload)

    async def sign_data(self, data: SignDataPayload, payload: str | CallbackData | None = None) -> str:
        """Ask the connected wallet to sign data; with ``ton_proof`` a wrong signature fails the operation.

        :return: Operation ID, as in ``send_transaction``.
        """
        async with self._screens.locked():
            return await self._request(OperationKind.SIGN_DATA, data, payload)

    async def on_request(
        self,
        connector: Connector,
        request_id: int,
        result: SendTransactionResult | SignMessageResult | SignDataResult | None,
        error: TonConnectError | None,
    ) -> None:
        """Take the answer of the wallet to a request; called by the library."""
        async with self._screens.locked():
            connection = await connector.to_connection()
            session_id = connection.session.session_keypair.session_id if connection is not None else None
            operation = await self._storage.answered_by(session_id, request_id)
            if operation is None:
                logger.debug("Answer %s of the wallet matches no operation of %s", request_id, self._connector.key)
                return
            failure = error or await self._check_signature(connector, result)
            if failure is not None or result is None:
                await self._screens.fail(operation, failure or TonConnectError("The wallet sent no result"))
            else:
                await self._screens.end(operation, Status.DONE, result)
            await self._connector.release()

    async def _request(
        self, kind: OperationKind, request: SendTransactionPayload | SignDataPayload, payload: str | CallbackData | None
    ) -> str:
        if payload is not None:
            same = await self._storage.same_request(kind, pack_payload(payload))
            if same is not None:
                # A double tap or a stale button: the wallet already has this request
                return same.id
        operation = self._screens.new(kind, payload)
        connection = self._connector.connection
        if connection is None:
            await self._screens.fail(operation, WalletNotConnectedError())
            return operation.id
        operation.session_id = connection.session.session_keypair.session_id
        connector = await self._connector.open()
        if not connector.connected:
            # restore() found the session gone, by a disconnect waiting in the bridge queue
            return await self._give_up(operation, WalletNotConnectedError())
        try:
            # What the wallet cannot take fails here, before the waiting screen
            timeout, send = _prepare(connector, kind, request)
        except TonConnectError as error:
            return await self._give_up(operation, error)
        operation.deadline = int(time.time() + timeout)
        wallet = self._connector.app_wallet
        open_link = None
        if wallet is not None:
            open_link = connector.make_request_url(wallet, await self._connector.return_url(wallet))
        await self._storage.save(operation)
        waiting = self._manager.view.show_waiting(self.bot, operation, wallet, open_link)
        if not await self._screens.show(operation, waiting):
            return operation.id
        try:
            # ton_connect sends to the bridge in the background; a failure there comes to on_request()
            operation.request_id = await send(operation.deadline - time.time())
        except TonConnectError as error:
            return await self._give_up(operation, error)
        await self._storage.save(operation)
        return operation.id

    async def _give_up(self, operation: Operation, error: TonConnectError) -> str:
        await self._screens.fail(operation, error)
        await self._connector.release()
        return operation.id

    async def _check_signature(
        self, connector: Connector, result: SendTransactionResult | SignMessageResult | SignDataResult | None
    ) -> Exception | None:
        proof = self._manager.ton_proof
        if not isinstance(result, SignDataResult) or proof is None:
            return None
        account = connector.account
        return await proof.check_sign_data(account, result) if account is not None else WalletNotConnectedError()

    async def _resume_requests(self, connector: Connector, operations: list[Operation]) -> list[tuple[Operation, int]]:
        """Wait again for the requests a restart left; return those resumed."""
        resumed = []
        for operation in operations:
            if operation.kind is OperationKind.CONNECT:
                continue
            if operation.request_id is None:
                # The bot stopped while the request was going out: whether the wallet got it is unknown
                await self._screens.fail(operation, TonConnectError("The bot stopped while sending the request"))
                continue
            left = operation.deadline - time.time()
            connector.resume_request(operation.request_id, operation.kind.event, max(left, RESUME_WINDOW))
            resumed.append((operation, operation.request_id))
        return resumed

    async def _lose_requests(self, connector: Connector, requests: list[tuple[Operation, int]]) -> None:
        """Fail the resumed requests: the stored session is unreadable, so no answer can be matched to them."""
        for _, request_id in requests:
            connector.drop_request(request_id)
        for operation, _ in requests:
            await self._screens.fail(operation, WalletNotConnectedError())


def _prepare(
    connector: Connector, kind: OperationKind, request: SendTransactionPayload | SignDataPayload
) -> tuple[float, t.Callable[[float], t.Awaitable[int]]]:
    """Check the request; return its timeout and the sending of it with the time left."""
    if not isinstance(request, SendTransactionPayload):
        data, timeout = connector.prepare_sign_data(request)
        return timeout, lambda left: connector.sign_data(data, timeout=left)
    if kind is OperationKind.SIGN_MESSAGE:
        message, timeout = connector.prepare_sign_message(request)
        return timeout, lambda left: connector.sign_message(message, timeout=left)
    transaction, timeout = connector.prepare_transaction(request)
    return timeout, lambda left: connector.send_transaction(transaction, timeout=left)
