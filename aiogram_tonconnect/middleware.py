from typing import Callable, Dict, Any, Awaitable, Optional, Type, List
from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject, User
from redis.asyncio import Redis

from .manager import ATCManager
from .tonconnect import AiogramTonConnect
from .tonconnect.storage import SessionStorage
from .tonconnect.models import ATCUser, AppWallet, AccountWallet
from .utils.keyboards import InlineKeyboardBase, InlineKeyboard
from .utils.qrcode import QRCodeProviderBase, QRCodeProvider
from .utils.texts import TextMessageBase, TextMessage


class AiogramTonConnectMiddleware(BaseMiddleware):
    """
    Aiogram middleware for AiogramTonConnect integration.

    :param redis: Redis instance for storage.
    :param manifest_url: URL to the AiogramTonConnect manifest.
    :param exclude_wallets: List of wallet names to exclude.
    :param qrcode_provider: QRCodeProviderBase instance for generating QR codes.
    :param text_message: TextMessageBase class for managing text messages.
    :param inline_keyboard: InlineKeyboardBase class for managing inline keyboards.
    """

    def __init__(
            self,
            redis: Redis,
            manifest_url: str,
            exclude_wallets: List[str] = None,
            qrcode_provider: Optional[QRCodeProviderBase] = None,
            text_message: Optional[Type[TextMessageBase]] = None,
            inline_keyboard: Optional[Type[InlineKeyboardBase]] = None,
    ) -> None:
        self.redis = redis
        self.manifest_url = manifest_url
        self.exclude_wallets = exclude_wallets

        if not qrcode_provider:
            qrcode_provider = QRCodeProvider()
        self.qrcode_provider = qrcode_provider

        if not text_message:
            text_message = TextMessage
        self.text_message = text_message

        if not inline_keyboard:
            inline_keyboard = InlineKeyboard
        self.inline_keyboard = inline_keyboard

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        """
        Execute middleware

        :param handler: Wrapped handler in middlewares chain
        :param event: Incoming event (Subclass of :class:`aiogram.types.base.TelegramObject`)
        :param data: Contextual data. Will be mapped to handler arguments
        :return: :class:`Any`
        """
        state: FSMContext = data.get("state")
        state_data = await state.get_data()

        account_wallet = state_data.get("account_wallet", None)
        account_wallet = AccountWallet(**account_wallet) if account_wallet else None
        data["account_wallet"] = account_wallet

        app_wallet = state_data.get("app_wallet", None)
        app_wallet = AppWallet(**app_wallet) if app_wallet else None
        data["app_wallet"] = app_wallet

        user: User = data.get("event_from_user")

        atc_user = ATCUser(
            id=user.id,
            language_code=state_data.get(
                "language_code",
                user.language_code,
            ),
            last_transaction_boc=state_data.get("last_transaction_boc", None),
            app_wallet=app_wallet,
            account_wallet=account_wallet,
        )
        data["atc_user"] = atc_user

        tonconnect = AiogramTonConnect(
            storage=SessionStorage(self.redis, atc_user.id),
            manifest_url=self.manifest_url,
            exclude_wallets=self.exclude_wallets
        )
        await tonconnect.restore_connection()
        atc_manager = ATCManager(
            redis=self.redis,
            tonconnect=tonconnect,
            qrcode_provider=self.qrcode_provider,
            text_message=self.text_message(atc_user.language_code),
            inline_keyboard=self.inline_keyboard(atc_user.language_code),
            user=atc_user,
            data=data,
        )
        data["atc_manager"] = atc_manager

        return await handler(event, data)
