from typing import Callable, Dict, Any, Awaitable, Optional, Type, List, Literal
from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject, User
from redis.asyncio import Redis

from .manager import ATCManager
from .tonconnect import AiogramTonConnect
from .tonconnect.storage import SessionStorage
from .tonconnect.models import ATCUser, AppWallet, AccountWallet
from .utils.keyboards import InlineKeyboardBase, InlineKeyboard
from .utils.texts import TextMessageBase, TextMessage


class AiogramTonConnectMiddleware(BaseMiddleware):
    """
    Aiogram middleware for AiogramTonConnect integration.

    :param redis: Redis instance for storage.
    :param manifest_url: URL to the AiogramTonConnect manifest.
    :param redirect_url: URL to the redirect after connecting.
    :param exclude_wallets: List of wallet names to exclude.
    :param qrcode_type: Type for the QR code, `url` or `bytes`.
        Choose "bytes" if you prefer to generate QR codes locally.
    :param qrcode_base_url: Base URL for generating the QR code (for qrcode_type `url`).
    :param text_message: TextMessageBase class for managing text messages.
    :param inline_keyboard: InlineKeyboardBase class for managing inline keyboards.
    """

    def __init__(
            self,
            redis: Redis,
            manifest_url: str,
            redirect_url: str = None,
            exclude_wallets: List[str] = None,
            qrcode_type: Literal["url", "bytes"] = "bytes",
            qrcode_base_url: Optional[str] = "https://qrcode.ness.su",
            text_message: Optional[Type[TextMessageBase]] = None,
            inline_keyboard: Optional[Type[InlineKeyboardBase]] = None,
    ) -> None:
        self.redis = redis
        self.manifest_url = manifest_url
        self.redirect_url = redirect_url
        self.exclude_wallets = exclude_wallets
        self.qrcode_type = qrcode_type
        self.qrcode_base_url = qrcode_base_url

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

        account_wallet = state_data.get("account_wallet")
        account_wallet = AccountWallet(**account_wallet) if account_wallet else None
        data["account_wallet"] = account_wallet

        app_wallet = state_data.get("app_wallet")
        app_wallet = AppWallet.from_dict(app_wallet) if app_wallet else None
        data["app_wallet"] = app_wallet

        user: User = data.get("event_from_user")
        language_code = state_data.get("language_code")
        language_code = language_code if language_code else user.language_code
        last_transaction_boc = state_data.get("last_transaction_boc")

        atc_user = ATCUser(
            id=user.id,
            language_code=language_code,
            last_transaction_boc=last_transaction_boc,
            app_wallet=app_wallet,
            account_wallet=account_wallet,
        )
        data["atc_user"] = atc_user

        tonconnect = AiogramTonConnect(
            storage=SessionStorage(self.redis, atc_user.id),
            manifest_url=self.manifest_url,
            redirect_url=self.redirect_url,
            exclude_wallets=self.exclude_wallets
        )
        atc_manager = ATCManager(
            redis=self.redis,
            tonconnect=tonconnect,
            qrcode_type=self.qrcode_type,
            qrcode_base_url=self.qrcode_base_url,
            text_message=self.text_message(atc_user.language_code),
            inline_keyboard=self.inline_keyboard(atc_user.language_code),
            user=atc_user,
            data=data,
        )
        data["atc_manager"] = atc_manager

        return await handler(event, data)
