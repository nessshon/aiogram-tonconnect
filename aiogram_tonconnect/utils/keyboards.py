from abc import ABCMeta, abstractmethod
from typing import List, Dict

from aiogram.utils.keyboard import InlineKeyboardMarkup as Markup, InlineKeyboardBuilder
from aiogram.utils.keyboard import InlineKeyboardButton as Button

from ..tonconnect.models import AppWallet


class InlineKeyboardBase(metaclass=ABCMeta):
    """
    Abstract base class for handling inline keyboards with buttons.

    :param language_code: The language code for the button texts.
    """

    @property
    @abstractmethod
    def texts_buttons(self) -> Dict[str, Dict[str, str]]:
        """
        Property to retrieve a dictionary of button texts for different languages.

        :return: Dictionary containing button texts for each language.
        """
        raise NotImplementedError

    def __init__(self, language_code: str) -> None:
        """
        Initialize the InlineKeyboardBase with a specified language code.

        If the provided language code is not supported, the default language is set to "en" (English).

        :param language_code: The language code for the button texts.
        """
        if language_code not in self.texts_buttons.keys():
            language_code = "en"
        self.language_code = language_code

    @abstractmethod
    def connect_wallet(
            self,
            wallets: List[AppWallet],
            selected_wallet: AppWallet,
            universal_url: str,
            wallet_name: str,
            width: int = 2,
    ) -> Markup:
        """
        Create an inline keyboard for connecting a wallet.

        :param wallets: List of available app wallets.
        :param selected_wallet: The selected app wallet.
        :param universal_url: Universal URL for connecting the wallet.
        :param wallet_name: Name of the wallet.
        :param width: Number of wallet buttons per row.
        :return: Inline keyboard markup.
        """
        raise NotImplementedError

    @abstractmethod
    def connect_wallet_proof_wrong(self) -> Markup:
        """
        Create an inline keyboard for proof of wrong connection.

        :return: Inline keyboard markup.
        """
        raise NotImplementedError

    @abstractmethod
    def send_transaction(self, wallet_name: str, url: str) -> Markup:
        """
        Create an inline keyboard for sending a transaction.

        :param wallet_name: Name of the wallet.
        :param url: URL for opening the wallet.
        :return: Inline keyboard markup.
        """
        raise NotImplementedError

    @abstractmethod
    def send_transaction_timeout(self) -> Markup:
        """
        Create an inline keyboard for a transaction timeout.

        :return: Inline keyboard markup.
        """
        raise NotImplementedError

    @abstractmethod
    def send_transaction_rejected(self) -> Markup:
        """
        Create an inline keyboard for a rejected transaction.

        :return: Inline keyboard markup.
        """
        raise NotImplementedError

    def _get_button(
            self,
            code: str,
            url: str = None,
            **kwargs,
    ) -> Button:
        """
        Helper method to create an inline keyboard button.

        :param code: Code identifying the specific button.
        :param url: URL associated with the button.
        :param kwargs: Additional arguments for formatting button text.
        :return: Inline keyboard button.
        """
        text = self.texts_buttons[self.language_code][code].format_map(kwargs)
        if not url:
            return Button(text=text, callback_data=code)
        return Button(text=text, url=url)


class InlineKeyboard(InlineKeyboardBase):

    @property
    def texts_buttons(self) -> Dict[str, Dict[str, str]]:
        return {
            "ru": {
                "back": "‹ Назад",
                "retry": "↻ Повторить",
                "connect_wallet": "Подключить {wallet_name}",
                "open_wallet": "Перейти в {wallet_name}",
            },
            "en": {
                "back": "‹ Back",
                "retry": "↻ Retry",
                "connect_wallet": "Connect {wallet_name}",
                "open_wallet": "Go to {wallet_name}",
            },
        }

    def connect_wallet(
            self,
            wallets: List[AppWallet],
            selected_wallet: AppWallet,
            universal_url: str,
            wallet_name: str,
            width: int = 2,
    ) -> Markup:
        generated_buttons = [
            *[
                Button(
                    text=f"• {wallet.name} •" if wallet.app_name == selected_wallet.app_name else wallet.name,
                    callback_data=f"app_wallet:{wallet.app_name}",
                ) for wallet in wallets
            ]
        ]
        builder = InlineKeyboardBuilder()
        builder.row(self._get_button("connect_wallet", universal_url, wallet_name=wallet_name))
        builder.row(*generated_buttons, width=width)
        builder.row(self._get_button("back"))
        return builder.as_markup()

    def connect_wallet_proof_wrong(self) -> Markup:
        inline_keyboard = [
            [self._get_button("back"),
             self._get_button("retry")],
        ]
        return Markup(inline_keyboard=inline_keyboard)

    def send_transaction(self, wallet_name: str, url: str) -> Markup:
        inline_keyboard = [
            [self._get_button("open_wallet", url=url, wallet_name=wallet_name)],
            [self._get_button("back")],
        ]
        return Markup(inline_keyboard=inline_keyboard)

    def send_transaction_timeout(self) -> Markup:
        inline_keyboard = [
            [self._get_button("back"),
             self._get_button("retry")],
        ]
        return Markup(inline_keyboard=inline_keyboard)

    def send_transaction_rejected(self) -> Markup:
        inline_keyboard = [
            [self._get_button("back"),
             self._get_button("retry")],
        ]
        return Markup(inline_keyboard=inline_keyboard)
