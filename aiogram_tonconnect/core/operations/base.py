from __future__ import annotations

import typing as t

from ..connector import UserConnector
from ..screens import UserScreens

if t.TYPE_CHECKING:
    from aiogram import Bot
    from aiogram.types import Message, User
    from ton_connect.connector import Connector

    from ...manager import TonConnectManager


class OperationsBase:
    def __init__(
        self,
        manager: TonConnectManager,
        bot: Bot,
        user: User,
        message: Message | None = None,
        user_message: Message | None = None,
    ) -> None:
        self.bot = bot
        self.user = user
        self._manager = manager
        self._user_message = user_message
        self._storage = manager.storage.user(bot.id, user.id)
        self._connector = UserConnector(manager, bot, user, self._storage)
        self._screens = UserScreens(manager, bot, user, self._storage, self._connector, message)

    async def on_back(self, operation_id: str) -> None:
        """End an operation as its Back button does; called by the library."""
        async with self._screens.locked():
            await self._screens.leave(operation_id)

    async def cancel(self) -> None:
        """End the operations of the user as their Back buttons do; the wallet stays connected."""
        async with self._screens.locked():
            for operation in await self._storage.all():
                await self._screens.leave(operation.id)

    async def _disconnect(self) -> None:
        """Disconnect the wallet, or forget a connect in progress, and drop the operations."""
        connector: Connector | None
        if self._connector.connection is not None:
            connector = await self._connector.open()
            await self._connector.disconnect(connector)
        else:
            # Opening a bridge for a connect in progress would restore it on every bridge of the catalog
            connector = self._connector.current()
            await self._storage.forget_session()
        await self._screens.drop()
        await self._connector.forget(connector)
