from __future__ import annotations

import logging
import typing as t

from ton_connect.exceptions import TonConnectError
from ton_connect.models import AppWallet, Wallet
from ton_connect.utils import find_app_wallet, is_telegram_url

from .models import OperationKind

if t.TYPE_CHECKING:
    from aiogram import Bot
    from aiogram.types import User
    from ton_connect.connector import Connector
    from ton_connect.models import ActiveConnection

    from ..manager import TonConnectManager
    from .models import Operation
    from .storage import UserStorage


logger = logging.getLogger(__name__)


class UserConnector:
    """The ``ton_connect`` connector of one user and the stored session of their wallet."""

    def __init__(self, manager: TonConnectManager, bot: Bot, user: User, storage: UserStorage) -> None:
        self.key = storage.key
        self.connection: ActiveConnection | None = None
        self._manager = manager
        self._bot = bot
        self._user = user
        self._storage = storage

    @property
    def wallet(self) -> Wallet | None:
        if self.connection is None:
            return None
        return Wallet.from_payload(self.connection.connect_event.payload)

    @property
    def app_wallet(self) -> AppWallet | None:
        if self.connection is None:
            return None
        app_name = self.connection.connect_event.payload.device.app_name
        return find_app_wallet(self._manager.tonconnect.app_wallets, app_name, self.connection.session.bridge_url)

    async def load(self) -> None:
        """Read the session from the storage: another update or the bridge may have changed it."""
        self.connection = await self._storage.connection()

    def current(self) -> Connector | None:
        return self._manager.tonconnect.connectors.get(self.key)

    def create(self) -> Connector:
        """Return a new connector; ``ton_connect`` closes the previous one of the user."""
        return self._manager.tonconnect.create_connector(self.key, bot=self._bot, user_id=self._user.id)

    async def open(self) -> Connector:
        """Return the connector of the user, restoring the stored session on a bridge if there is none."""
        connector = self.current()
        if connector is None:
            connector = self.create()
            await connector.restore()
        return connector

    async def release(self) -> None:
        """Close the bridge once no operation waits for the wallet."""
        connector = self.current()
        if connector is not None and not await self._storage.waiting():
            await connector.close()

    @staticmethod
    async def disconnect(connector: Connector) -> None:
        """Tell the wallet the bot disconnects; a failure is ignored."""
        if connector.connected:
            try:
                await connector.disconnect()
            except TonConnectError as error:
                # The wallet may be offline; the bot forgets the session all the same
                logger.debug("Disconnecting the wallet of %s failed: %s", connector.session_key, error)

    def approved(self, operation: Operation) -> bool:
        """Return whether the stored session is the one the connect of the operation asked for."""
        connection = self.connection
        return connection is not None and connection.session.session_keypair.session_id == operation.session_id

    async def drop_session(self) -> None:
        """Disconnect the wallet of the stored session and forget it."""
        connector = await self.open()
        await self.disconnect(connector)
        await self._storage.forget_session()
        await self.forget(connector)

    async def forget(self, connector: Connector | None) -> None:
        if connector is not None:
            await connector.close()
        self.connection = None

    def stop_waiting(self, operation: Operation) -> None:
        connector = self.current()
        if operation.error is not None or connector is None:
            return
        if operation.request_id is not None:
            connector.drop_request(operation.request_id)
        elif operation.kind is OperationKind.CONNECT:
            connector.drop_connect()

    async def return_url(self, wallet: AppWallet) -> str:
        """Where the wallet returns the user after the Open button."""
        if self._manager.redirect_url is not None:
            return self._manager.redirect_url
        # Telegram Wallet is a mini app: "back" closes it to the chat, as tonconnect-ui does inside Telegram
        if is_telegram_url(wallet.universal_url):
            return "back"
        # The user came from Telegram on this device; tonconnect-ui sends tg://resolve there, the domain opens the bot
        return f"tg://resolve?domain={(await self._bot.me()).username}"
