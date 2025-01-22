from typing import Callable, Dict, Any, Awaitable, Optional, Type, Union

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject, User, Chat
from tonutils.tonconnect import TonConnect

from .manager import ATCManager
from .tonconnect.models import ATCUser
from .utils.keyboards import InlineKeyboardBase, InlineKeyboard
from .utils.qrcode import QRImageProviderBase, QRUrlProviderBase, QRImageProvider
from .utils.texts import TextMessageBase, TextMessage


class AiogramTonConnectMiddleware(BaseMiddleware):
    """
    Middleware for integrating Aiogram with AiogramTonConnect.

    :param tonconnect: TonConnect instance for managing Ton blockchain connections.
    :param text_message: Custom class for managing text messages.
    :param inline_keyboard: Custom class for managing inline keyboards.
    :param qrcode_provider: Instance for generating QR codes.
    """

    def __init__(
            self,
            tonconnect: TonConnect,
            text_message: Optional[Type[TextMessageBase]] = None,
            inline_keyboard: Optional[Type[InlineKeyboardBase]] = None,
            qrcode_provider: Optional[Union[QRImageProviderBase, QRUrlProviderBase]] = None,
    ) -> None:
        self.tonconnect = tonconnect
        self.qrcode_provider = qrcode_provider or QRImageProvider()
        self.text_message = text_message or TextMessage
        self.inline_keyboard = inline_keyboard or InlineKeyboard

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        """
        Middleware execution logic.

        :param handler: The next handler in the middleware chain.
        :param event: Incoming Telegram event.
        :param data: Contextual data passed to the handler.
        :return: Result of the handler execution.
        """
        user: Optional[User] = data.get("event_from_user")
        chat: Optional[Chat] = data.get("event_chat")

        if self._is_private_chat_with_user(chat, user):
            if user and chat:
                await self._setup_user_context(user, data)

        return await handler(event, data)

    @staticmethod
    def _is_private_chat_with_user(chat: Optional[Chat], user: Optional[User]) -> bool:
        """
        Check if the chat is a private chat with a non-bot user.

        :param chat: Chat object from the event.
        :param user: User object from the event.
        :return: True if private chat with a user, False otherwise.
        """
        return bool(chat and chat.type == "private" and user and not user.is_bot)

    async def _setup_user_context(self, user: User, data: Dict[str, Any]) -> None:
        """
        Set up user-specific context for the middleware.

        :param user: User object from the event.
        :param data: Contextual data dictionary.
        """
        state: Optional[FSMContext] = data.get("state")
        state_data = await state.get_data() if state else {}

        connector = await self._get_connector(user.id)
        data["connector"] = connector

        language_code = state_data.get("language_code", user.language_code)
        last_transaction_boc = state_data.get("last_transaction_boc")

        atc_user = ATCUser(
            id=user.id,
            language_code=language_code,
            wallet_address=connector.wallet.account.address if connector.connected else None,
            last_transaction_boc=last_transaction_boc,
        )
        data["atc_user"] = atc_user

        atc_manager = ATCManager(
            connector=connector,
            tonconnect=self.tonconnect,
            text_message=self.text_message(language_code),
            inline_keyboard=self.inline_keyboard(language_code),
            qrcode_provider=self.qrcode_provider,
            user=atc_user,
            data=data,
        )
        data["atc_manager"] = atc_manager

    async def _get_connector(self, user_id: int) -> Any:
        """
        Initialize or retrieve a TonConnect connector.

        :param user_id: Telegram user ID.
        :return: Initialized or retrieved connector.
        """
        connector = await self.tonconnect.get_connector(user_id)
        if connector is None:
            connector = await self.tonconnect.create_connector(user_id)
        return connector
