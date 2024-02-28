from abc import ABCMeta, abstractmethod
from typing import Dict

from aiogram.utils.markdown import hide_link


class TextMessageBase(metaclass=ABCMeta):
    """
    Abstract base class for handling text messages in different languages.

    :param language_code: The language code for the text messages.
    """

    @property
    @abstractmethod
    def texts_messages(self) -> Dict[str, Dict[str, str]]:
        """
        Property to retrieve a dictionary of text messages for different languages.

        :return: Dictionary containing text messages for each language.
        """
        raise NotImplementedError

    def __init__(self, language_code: str) -> None:
        """
        Initialize the TextMessageBase with a specified language code.

        If the provided language code is not supported, the default language is set to "en" (English).

        :param language_code: The language code for the text messages.
        """
        if language_code not in self.texts_messages.keys():
            language_code = "en"
        self.language_code = language_code

    def get(self, code: str) -> str:
        """
        Get a specific text message based on the language code and message code.

        :param code: Code identifying the specific message.
        :return: The text message.
        """
        return self.texts_messages[self.language_code][code]


class TextMessage(TextMessageBase):
    """
    Concrete implementation of TextMessageBase providing text messages for different languages.
    """

    @property
    def texts_messages(self) -> Dict[str, Dict[str, str]]:
        get_a_wallet_link = "https://ton.org/wallets?filters[wallet_features][slug][$in]=dapp-auth&pagination[limit]=-1"
        ton_connect_banner_link = "https://telegra.ph//file/a4ddc111ff41692ad5200.jpg"

        return {
            "ru": {
                # When the bot response time exceeds 2-3 seconds, such as during QR code generation,
                # utilize 'loader_text' as a placeholder.
                "loader_text": (
                    "💎"
                ),
                # If a message is older than 2 days, the Telegram Bot API does not support direct deletion.
                # Instead, we modify the message text as 'outdated_text'.
                "outdated_text": (
                    "..."
                ),
                "connect_wallet": (
                    f"<a href='{get_a_wallet_link}'>Установить кошелек</a>\n\n"
                    "<b>Подключите свой {wallet_name}!</b>\n\n"
                    "Отсканируйте с помощью мобильного кошелька:"
                ),
                "connect_wallet_proof_wrong": (
                    f"{hide_link(ton_connect_banner_link)}"
                    "<b>Предупреждение</b>\n\n"
                    "Подпись кошелька поддельна или истекло время ожидания подключения."
                ),
                "connect_wallet_timeout": (
                    f"{hide_link(ton_connect_banner_link)}"
                    "<b>Предупреждение</b>\n\n"
                    "Время ожидания подключения истекло."
                ),
                "send_transaction": (
                    f"{hide_link(ton_connect_banner_link)}"
                    "<b>Транзакция</b>\n\n"
                    "Перейдите в приложение {wallet_name} и подтвердите транзакцию."
                ),
                "send_transaction_timeout": (
                    f"{hide_link(ton_connect_banner_link)}"
                    "<b>Предупреждение</b>\n\n"
                    "Время ожидания подтверждения транзакции истекло."
                ),
                "send_transaction_rejected": (
                    f"{hide_link(ton_connect_banner_link)}"
                    "<b>Предупреждение</b>\n\n"
                    "Вы отменили транзакцию!"
                ),
            },
            "en": {
                # When the bot response time exceeds 2-3 seconds, such as during QR code generation,
                # utilize 'loader_text' as a placeholder.
                "loader_text": (
                    "💎"
                ),
                # If a message is older than 2 days, the Telegram Bot API does not support direct deletion.
                # Instead, we modify the message text as 'outdated_text'.
                "outdated_text": (
                    "..."
                ),
                "connect_wallet": (
                    f"<a href='{get_a_wallet_link}'>Get a Wallet</a>\n\n"
                    "<b>Connect your {wallet_name}!</b>\n\n"
                    "Scan with your mobile app wallet:"
                ),
                "connect_wallet_proof_wrong": (
                    f"{hide_link(ton_connect_banner_link)}"
                    "<b>Warning</b>\n\n"
                    "The wallet signature is wrong or the connection timeout has expired."
                ),
                "connect_wallet_timeout": (
                    f"{hide_link(ton_connect_banner_link)}"
                    "<b>Warning</b>\n\n"
                    "The connection timeout has expired."
                ),
                "send_transaction": (
                    f"{hide_link(ton_connect_banner_link)}"
                    f"<b>Transaction</b>\n\n"
                    "Go to the {wallet_name} app and confirm the transaction."
                ),
                "send_transaction_timeout": (
                    f"{hide_link(ton_connect_banner_link)}"
                    "<b>Warning</b>\n\n"
                    "The transaction timeout has expired."
                ),
                "send_transaction_rejected": (
                    f"{hide_link(ton_connect_banner_link)}"
                    "<b>Warning</b>\n\n"
                    "You rejected the transaction!"
                ),
            },
        }
