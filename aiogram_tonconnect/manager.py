from __future__ import annotations

import asyncio
import logging
import typing as t
from contextlib import nullcontext

from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.dispatcher.middlewares.user_context import EVENT_CONTEXT_KEY, EventContext
from aiogram.enums import ChatType
from aiogram.types import CallbackQuery, Message, TelegramObject, Update, User
from ton_connect import AppWalletsLoader, Event, TonConnect
from ton_connect.connector import Connector
from ton_connect.exceptions import TonConnectError
from ton_connect.models import AppWallet, SendTransactionResult, SignDataResult, SignMessageResult

from .context import TonConnectContext
from .core.storage import KeyedLock, Storage, session_key
from .events.dispatch import TonConnectUpdate
from .view import GoBack, SelectWallet, ShowWallets, View

if t.TYPE_CHECKING:
    from aiogram.utils.callback_answer import CallbackAnswer
    from ton_core import NetworkGlobalID

    from .core.proof import TonProof

logger = logging.getLogger(__name__)

# Each resume opens a bridge stream; the reference bridge allows 10 requests a second by default (RPS_LIMIT)
RESUME_RATE = 10


def _selectable(wallet: AppWallet) -> bool:
    try:
        # Operation IDs are 12 hex digits, and Telegram caps callback data at 64 bytes
        SelectWallet(operation_id="0" * 12, app_name=wallet.app_name).pack()
    except ValueError:
        logger.warning("Wallet %s is left out: its name does not fit a button", wallet.app_name)
        return False
    return True


class ContextMiddleware(BaseMiddleware):
    """Gives ``tc`` to the handlers in private chats, TON Connect events included."""

    def __init__(self, manager: TonConnectManager) -> None:
        self.manager = manager

    async def __call__(
        self,
        handler: t.Callable[[TelegramObject, dict[str, t.Any]], t.Awaitable[t.Any]],
        event: TelegramObject,
        data: dict[str, t.Any],
    ) -> t.Any:
        user, chat = data.get("event_from_user"), data.get("event_chat")
        if user is None or user.is_bot or chat is None or chat.type != ChatType.PRIVATE:
            return await handler(event, data)
        bot = data["bot"]
        message: Message | None = None
        user_message: Message | None = None
        if isinstance(event, TonConnectUpdate):
            # Operations and disconnect started by the handler of an event take over its screen
            message = event.event.message
            if message.from_user is not None and message.from_user.id == user.id:
                # tc.disconnect called from a message of the user gives it to the handler, and it is never a screen
                message, user_message = None, message
            if "state" not in data:
                # aiogram finds the chat of an update by its Telegram fields, and a TON Connect event has none
                data[EVENT_CONTEXT_KEY] = EventContext(chat=chat, user=user)
                state = self.manager.dispatcher.fsm.resolve_context(bot=bot, chat_id=chat.id, user_id=user.id)
                if state is not None:
                    data.update(state=state, raw_state=await state.get_state())
        elif isinstance(event, Update):
            # An inaccessible message can be neither edited nor deleted, so there is nothing to give
            query = event.callback_query
            message = query.message if query is not None and isinstance(query.message, Message) else None
            # The message of the user is never a screen, but tc.disconnect gives it to the handler to answer
            user_message = event.message
        # Who writes during a restart is resumed out of the queue, before the handler sees the operations
        await self.manager.resume_user(bot, user.id)
        data["tc"] = await TonConnectContext(self.manager, bot, user, message, user_message).load()
        return await handler(event, data)


class TonConnectManager:
    """TON Connect of a dispatcher, built by ``setup_tonconnect``."""

    def __init__(
        self,
        dispatcher: Dispatcher,
        bots: list[Bot],
        tonconnect: TonConnect,
        storage: Storage,
        view: View,
        wallets: list[AppWallet] | None,
        network: NetworkGlobalID | None,
        redirect_url: str | None,
        ton_proof: TonProof | None,
    ) -> None:
        self.dispatcher = dispatcher
        self.bots = bots
        self.tonconnect = tonconnect
        self.storage = storage
        self.view = view
        self.network = network
        self.redirect_url = redirect_url
        self.ton_proof = ton_proof
        self.lock = KeyedLock()
        self._wallets = wallets
        self._waiting: set[str] = set()
        self._resumes: dict[str, asyncio.Task[None]] = {}
        self._resuming: asyncio.Task[None] | None = None
        self._answers: set[asyncio.Task[None]] = set()
        self._startup_data: dict[str, t.Any] = {}

        # ton_connect copies its handlers into every connector, so they are set before the first one exists
        tonconnect.register(Event.CONNECT, self._on_connect)
        tonconnect.register(Event.TRANSACTION, self._on_request)
        tonconnect.register(Event.SIGN_MESSAGE, self._on_request)
        tonconnect.register(Event.SIGN_DATA, self._on_request)
        tonconnect.register(Event.DISCONNECT, self._on_disconnect)
        tonconnect.register(Event.ERROR, self._on_error)

        dispatcher.update.outer_middleware(ContextMiddleware(self))
        # The handlers of the dispatcher itself go before its routers, so a catch-all of the bot cannot take the buttons
        dispatcher.callback_query.register(self._on_go_back, GoBack.filter())
        dispatcher.callback_query.register(self._on_select_wallet, SelectWallet.filter())
        dispatcher.callback_query.register(self._on_show_wallets, ShowWallets.filter())
        dispatcher.startup.register(self._startup)
        dispatcher.shutdown.register(self._shutdown)

    @property
    def workflow_data(self) -> dict[str, t.Any]:
        """What aiogram gives the handlers of an update: the dispatcher, ``dp.workflow_data``, ``start_polling`` arguments."""
        return {"dispatcher": self.dispatcher, **self._startup_data, **self.dispatcher.workflow_data}

    async def context(self, bot: Bot, user_id: int) -> TonConnectContext:
        """Return ``tc`` of a user for work outside handlers; its screens go to the private chat."""
        await self.resume_user(bot, user_id)
        return await self._context(bot, user_id)

    async def _context(self, bot: Bot, user_id: int) -> TonConnectContext:
        operations = await self.storage.user(bot.id, user_id).all()
        user = operations[0].user if operations else User(id=user_id, is_bot=False, first_name="")
        return await TonConnectContext(self, bot, user).load()

    @staticmethod
    async def _on_go_back(
        query: CallbackQuery,
        callback_data: GoBack,
        tc: TonConnectContext,
        callback_answer: CallbackAnswer | None = None,
    ) -> None:
        # With CallbackAnswerMiddleware of the bot the query is answered there, and a second answer fails
        if callback_answer is None:
            await query.answer()
        await tc.on_back(callback_data.operation_id)

    @staticmethod
    async def _on_select_wallet(
        query: CallbackQuery,
        callback_data: SelectWallet,
        tc: TonConnectContext,
        callback_answer: CallbackAnswer | None = None,
    ) -> None:
        if callback_answer is None:
            await query.answer()
        await tc.on_select_wallet(callback_data.operation_id, callback_data.app_name)

    @staticmethod
    async def _on_show_wallets(
        query: CallbackQuery,
        callback_data: ShowWallets,
        tc: TonConnectContext,
        callback_answer: CallbackAnswer | None = None,
    ) -> None:
        if callback_answer is None:
            await query.answer()
        await tc.on_wallets_page(callback_data.operation_id, callback_data.page)

    async def _on_connect(self, connector: Connector, error: TonConnectError | None) -> None:
        self._take_answer(connector, lambda tc: tc.on_connect(connector, error))

    async def _on_request(
        self,
        connector: Connector,
        request_id: int,
        result: SendTransactionResult | SignMessageResult | SignDataResult | None,
        error: TonConnectError | None,
    ) -> None:
        self._take_answer(connector, lambda tc: tc.on_request(connector, request_id, result, error))

    async def _on_disconnect(self, connector: Connector, error: TonConnectError | None) -> None:
        self._take_answer(connector, lambda tc: tc.on_disconnect(connector, error))

    def _take_answer(self, connector: Connector, take: t.Callable[[TonConnectContext], t.Awaitable[None]]) -> None:
        # ton_connect calls back from the task reading the bridge, and closing the connector cancels that task: the
        # handlers of the events would be cut there, and a slow one would hold the bridge
        task = asyncio.create_task(self._answer(connector, take))
        self._answers.add(task)
        task.add_done_callback(self._answers.discard)

    async def _answer(self, connector: Connector, take: t.Callable[[TonConnectContext], t.Awaitable[None]]) -> None:
        bot, user_id = connector["bot"], connector["user_id"]
        # An update holds the FSM isolation lock of its user while handled; the answer of the wallet takes it too
        state = self.dispatcher.fsm.resolve_context(bot=bot, chat_id=user_id, user_id=user_id)
        isolation = self.dispatcher.fsm.events_isolation.lock(key=state.key) if state is not None else nullcontext()
        try:
            async with isolation:
                await take(await self._context(bot, user_id))
        except Exception:
            logger.exception("Handling the wallet answer failed for %s", connector.session_key)

    async def _on_error(self, connector: Connector, error: TonConnectError) -> None:
        # A bug behind the error keeps its traceback; a bridge failure stays one line
        cause = error if error.__cause__ is not None else None
        logger.warning("TON Connect error for %s: %s", connector.session_key, error, exc_info=cause)

    async def _startup(self, **data: t.Any) -> None:
        # aiogram starts with what it gives every update: the dispatcher, the bots, the arguments of start_polling
        data.pop("bot", None)
        self._startup_data = data
        wallets = self._wallets
        if wallets is None:
            # The loader fetches the public catalog synchronously
            wallets = await asyncio.to_thread(AppWalletsLoader().get_wallets)
        # A Telegram button opens a wallet only by its universal link
        linked = [wallet for wallet in wallets if wallet.universal_url]
        if skipped := [wallet.app_name for wallet in wallets if not wallet.universal_url]:
            logger.debug("Wallets without a universal link are left out: %s", ", ".join(skipped))
        usable = [wallet for wallet in linked if _selectable(wallet)]
        if not usable:
            raise RuntimeError("No usable wallet in the catalog")
        self.tonconnect.app_wallets = usable
        users = [(bot, user_id) for bot in self.bots for user_id in await self.storage.users(bot.id)]
        self._waiting = {session_key(bot.id, user_id) for bot, user_id in users}
        # restore() waits up to 2 s for a bridge; the bot takes updates meanwhile
        self._resuming = asyncio.create_task(self._resume_all(users))

    async def _resume_all(self, users: list[tuple[Bot, int]]) -> None:
        tasks = []
        for bot, user_id in users:
            if session_key(bot.id, user_id) not in self._waiting:
                # Resumed out of the queue already
                continue
            tasks.append(asyncio.create_task(self.resume_user(bot, user_id)))
            await asyncio.sleep(1 / RESUME_RATE)
        await asyncio.gather(*tasks)

    async def resume_user(self, bot: Bot, user_id: int) -> None:
        """Resume the operations a restart left to the user without waiting for the startup queue, or wait for it."""
        key = session_key(bot.id, user_id)
        if key in self._waiting:
            self._waiting.discard(key)
            self._resumes[key] = asyncio.create_task(self._resume(bot, user_id, key))
        task = self._resumes.get(key)
        # An operation started before the resume ends would lose its request: resume() replaces the connector. The
        # events the resume sends come back here from its own task, which must not wait for itself
        if task is not None and task is not asyncio.current_task():
            await asyncio.shield(task)

    async def _resume(self, bot: Bot, user_id: int, key: str) -> None:
        try:
            tc = await self._context(bot, user_id)
            await tc.resume()
        except Exception:
            # One user left unresumed must not stop the others or the update of this one
            logger.exception("Resuming failed for %s", key)
        finally:
            del self._resumes[key]

    async def _shutdown(self) -> None:
        tasks = [*self._resumes.values(), *([self._resuming] if self._resuming is not None else [])]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        # An answer being taken has deleted its operation already: cutting it would lose the event
        await asyncio.gather(*self._answers, return_exceptions=True)
        await self.tonconnect.close_all()
