from typing import Callable, Dict, Any, Awaitable, Optional, Type, List, Union

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject, User, Chat

from .manager import ATCManager
from .tonconnect import AiogramTonConnect
from .tonconnect.storage import SessionStorage
from .tonconnect.models import ATCUser, AppWallet, AccountWallet, InfoWallet
from .tonconnect.storage.base import ATCStorageBase
from .utils.keyboards import InlineKeyboardBase, InlineKeyboard
from .utils.qrcode import QRImageProviderBase, QRUrlProviderBase, QRImageProvider
from .utils.texts import TextMessageBase, TextMessage


class AiogramTonConnectMiddleware(BaseMiddleware):
    """
    Aiogram middleware for AiogramTonConnect integration.

    :param storage: An instance of ATCStorageBase for data storage.
        Available default classes:
        - ATCMemoryStorage: Stores data in memory.
        - ATCRedisStorage: Stores data in Redis.
    :param manifest_url: URL to the AiogramTonConnect manifest.
    :param redirect_url: URL to the redirect after connecting.
    :param exclude_wallets: List of wallet names to exclude.
    :param qrcode_provider: QRImageProviderBase or QRUrlProviderBase instance.
        Available default classes:
        - QRImageProvider: Generates QR codes locally using the library and
        displays message type as 'photo' with the QR code image.
        - QRUrlProvider: Generates QR codes using a third-party API and
        displays message type as 'text' with the image as 'web_page_preview'.
    :param inline_keyboard: InlineKeyboardBase class for managing inline keyboards.
    """

    def __init__(
            self,
            storage: ATCStorageBase,
            manifest_url: str,
            redirect_url: str = None,
            exclude_wallets: List[str] = None,
            text_message: Optional[Type[TextMessageBase]] = None,
            inline_keyboard: Optional[Type[InlineKeyboardBase]] = None,
            qrcode_provider: Optional[Union[QRImageProviderBase, QRUrlProviderBase]] = None,
            tonapi_token: Optional[str] = None,
    ) -> None:
        self.storage = storage
        self.manifest_url = manifest_url
        self.redirect_url = redirect_url
        self.exclude_wallets = exclude_wallets

        self.qrcode_provider = qrcode_provider or QRImageProvider()
        self.text_message = text_message or TextMessage
        self.inline_keyboard = inline_keyboard or InlineKeyboard

        self.tonapi_token = tonapi_token

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
        user: User = data.get("event_from_user")
        chat: Chat = data.get("event_chat")

        if chat and chat.type == "private" and user and not user.is_bot:
            state: FSMContext = data.get("state")
            state_data = await state.get_data()

            account_wallet = state_data.get("account_wallet")
            account_wallet = AccountWallet(**account_wallet) if account_wallet else None
            data["account_wallet"] = account_wallet

            info_wallet = state_data.get("info_wallet")
            info_wallet = InfoWallet(**info_wallet) if info_wallet else None
            data["info_wallet"] = info_wallet

            app_wallet = state_data.get("app_wallet")
            app_wallet = AppWallet(**app_wallet) if app_wallet else None
            data["app_wallet"] = app_wallet

            language_code = state_data.get("language_code")
            language_code = language_code if language_code else user.language_code
            last_transaction_boc = state_data.get("last_transaction_boc")

            atc_user = ATCUser(
                id=user.id,
                language_code=language_code,
                last_transaction_boc=last_transaction_boc,
                info_wallet=info_wallet,
                app_wallet=app_wallet,
                account_wallet=account_wallet,
            )
            data["atc_user"] = atc_user

            tonconnect = AiogramTonConnect(
                storage=SessionStorage(self.storage, atc_user.id),
                manifest_url=self.manifest_url,
                redirect_url=self.redirect_url,
                exclude_wallets=self.exclude_wallets,
                tonapi_token=self.tonapi_token,
            )
            atc_manager = ATCManager(
                storage=self.storage,
                tonconnect=tonconnect,
                text_message=self.text_message(atc_user.language_code),
                inline_keyboard=self.inline_keyboard(atc_user.language_code),
                qrcode_provider=self.qrcode_provider,
                user=atc_user,
                data=data,
            )
            data["atc_manager"] = atc_manager

        return await handler(event, data)
