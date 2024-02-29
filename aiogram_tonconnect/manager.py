from __future__ import annotations

import asyncio
from contextlib import suppress
from typing import Dict, Any, Union, Optional

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    BufferedInputFile,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.utils.markdown import hide_link

from pytonconnect.exceptions import (
    UserRejectsError,
    WalletNotConnectedError,
)

from .tonconnect import AiogramTonConnect
from .tonconnect.storage import (
    ConnectWalletCallbackStorage,
    SendTransactionCallbackStorage,
    TaskStorage,
)
from .tonconnect.models import (
    AccountWallet,
    ATCUser,
    AppWallet,
    ConnectWalletCallbacks,
    SendTransactionCallbacks,
    Transaction,
    InfoWallet,
)
from .tonconnect.storage.base import ATCStorageBase
from .utils.address import Address
from .utils.exceptions import (
    LanguageCodeNotSupported,
    RetryConnectWalletError,
    RetrySendTransactionError,
    MESSAGE_DELETE_ERRORS,
    MESSAGE_EDIT_ERRORS,
)
from .utils.keyboards import InlineKeyboardBase
from .utils.proof import generate_payload, check_payload
from .utils.qrcode import (
    QRImageProviderBase,
    QRUrlProviderBase,
)
from .utils.states import TcState
from .utils.texts import TextMessageBase


class ATCManager:
    """
    Manager class for AiogramTonConnect integration.

    :param user: The AiogramTonConnect user.
    :param storage: ATCStorageBase instance.
    :param tonconnect: AiogramTonConnect instance.
    :param text_message: TextMessageBase class for managing text messages.
    :param inline_keyboard: InlineKeyboardBase class for managing inline keyboards.
    :param qrcode_provider: QRImageProviderBase or QRUrlProviderBase instance.
    :param data: Additional data.
    """

    def __init__(
            self,
            user: ATCUser,
            storage: ATCStorageBase,
            tonconnect: AiogramTonConnect,
            text_message: TextMessageBase,
            inline_keyboard: InlineKeyboardBase,
            qrcode_provider: Union[QRImageProviderBase, QRUrlProviderBase],
            data: Dict[str, Any],
    ) -> None:
        self.user = user
        self.storage = storage
        self.tonconnect = tonconnect

        self.__data: Dict[str, Any] = data
        self.__text_message = text_message
        self.__inline_keyboard = inline_keyboard
        self.__qrcode_provider = qrcode_provider

        self.bot: Bot = data.get("bot")
        self.state: FSMContext = data.get("state")

        self.task_storage = TaskStorage(user.id)
        self.connect_wallet_callbacks_storage = ConnectWalletCallbackStorage(storage, user.id)
        self.send_transaction_callbacks_storage = SendTransactionCallbackStorage(storage, user.id)

    @property
    def middleware_data(self) -> Dict[str, Any]:
        """
        Get middleware data.
        """
        return self.__data

    async def update_interfaces_language(self, language_code: str) -> None:
        """
        Update interfaces language.

        :param language_code: The language code to update to.
        :raise LanguageCodeNotSupported: If the provided language code is not supported.
        """
        if (
                language_code in self.__text_message.texts_messages and
                language_code in self.__inline_keyboard.texts_buttons
        ):
            await self.state.update_data(language_code=language_code)
            self.user.language_code = language_code
            self.__text_message.language_code = self.__inline_keyboard.language_code = language_code
            return None

        raise LanguageCodeNotSupported(
            f"Language code '{language_code}' not in text message or button text"
        )

    async def connect_wallet(
            self,
            callbacks: ConnectWalletCallbacks,
            check_proof: Optional[bool] = False,
            proof_payload: Optional[str] = None,
    ) -> None:
        """
        Open the connect wallet window.

        :param callbacks: Callbacks to execute.
        :param check_proof: Set to True to check ton_proof; False to use ton_addr.
        :param proof_payload: Payload for ton_proof.

        If check_proof is True and proof_payload is not specified, it will be generated automatically.
        If check_proof is True and proof_payload is specified, the provided proof_payload will be used.
        If check_proof is not specified, connection without proof (ton_addr) will be used.
        Link to the specification:
            https://github.com/ton-blockchain/ton-connect/blob/main/requests-responses.md#initiating-connection
        """
        await self.disconnect_wallet()

        if isinstance(self.__qrcode_provider, QRImageProviderBase):
            text = self.__text_message.get("loader_text")
            await self._send_message(text)

        await self.connect_wallet_callbacks_storage.add(callbacks)

        state_data = await self.state.get_data()
        wallets = await self.tonconnect.get_wallets()

        app_wallet_dict = state_data.get("app_wallet") or wallets[0].model_dump()
        app_wallet = AppWallet(**app_wallet_dict)

        if check_proof:
            proof_payload = proof_payload or generate_payload()
            ton_proof = {"ton_proof": proof_payload}
            universal_url = await self.tonconnect.connect(app_wallet.model_dump(), ton_proof)
        else:
            proof_payload = None
            universal_url = await self.tonconnect.connect(app_wallet.model_dump())

        await self.state.update_data(
            app_wallet=app_wallet.model_dump(),
            proof_payload=proof_payload,
            check_proof=check_proof,
        )

        task = asyncio.create_task(self.__wait_connect_wallet_task())
        self.task_storage.add(task)

        reply_markup = self.__inline_keyboard.connect_wallet(
            wallets, app_wallet, universal_url,
            wallet_name=app_wallet.name,
        )
        text = self.__text_message.get("connect_wallet").format(
            wallet_name=app_wallet.name
        )
        await self._send_connect_wallet_window(text, reply_markup, universal_url, app_wallet)
        await self.state.set_state(TcState.connect_wallet)

    async def retry_connect_wallet(self) -> None:
        """
        Retry open the connect wallet window.
        """
        state_data = await self.state.get_data()
        check_proof = state_data.get("check_proof", False)
        callbacks = await self.connect_wallet_callbacks_storage.get()

        if callbacks is None:
            raise RetryConnectWalletError(
                "No callbacks found for connect wallet. "
                "You need a connect wallet first."
            )

        await self.connect_wallet(callbacks, check_proof)

    async def _send_connect_wallet_window(
            self,
            text: str,
            reply_markup: InlineKeyboardMarkup,
            universal_url: str,
            app_wallet: AppWallet,
    ) -> None:
        """
        Send the connect wallet window with appropriate content based on the qrcode_type.

        :param text: The text message to be sent.
        :param reply_markup: The inline keyboard markup for the message.
        :param universal_url: The universal URL for connecting the wallet.
        :param app_wallet: The AppWallet instance representing the connected wallet.
        """
        if isinstance(self.__qrcode_provider, QRImageProviderBase):
            photo = await self.__qrcode_provider.create_connect_wallet_image(
                universal_url, app_wallet.image
            )
            await self._send_photo(
                photo=BufferedInputFile(photo, "qr.png"),
                caption=text,
                reply_markup=reply_markup,
            )
        else:
            qrcode_url = await self.__qrcode_provider.create_connect_wallet_image_url(
                universal_url, app_wallet.image
            )
            await self._send_message(
                text=hide_link(qrcode_url) + text,
                reply_markup=reply_markup,
            )

    async def disconnect_wallet(self) -> None:
        """
        Disconnect the connected wallet.
        """
        with suppress(WalletNotConnectedError):
            await self.tonconnect.restore_connection()
            await self.tonconnect.disconnect()

    async def send_transaction(
            self,
            transaction: Transaction,
            callbacks: SendTransactionCallbacks,
    ) -> None:
        """
        Open the send transaction window.

        :param callbacks: Callbacks to execute.
        :param transaction: The transaction details.
        """
        await self.state.update_data(transaction=transaction.model_dump())
        await self.send_transaction_callbacks_storage.add(callbacks)

        task = asyncio.create_task(self.__wait_send_transaction_task())
        self.task_storage.add(task)

        text = self.__text_message.get("send_transaction").format(
            wallet_name=self.user.app_wallet.name,
        )
        universal_url = self.user.app_wallet.universal_url
        if self.user.app_wallet.app_name == "telegram-wallet":
            universal_url = universal_url.replace(
                "attach=wallet", "startattach=tonconnect-ret__back"
            )
        reply_markup = self.__inline_keyboard.send_transaction(
            self.user.app_wallet.name, universal_url,
        )

        await self._send_message(text=text, reply_markup=reply_markup)
        await self.state.set_state(TcState.send_transaction)

    async def retry_last_send_transaction(self) -> None:
        data = await self.state.get_data()

        try:
            transaction = Transaction.model_validate(data.get("transaction"))
        except KeyError:
            raise RetrySendTransactionError(
                "Last transaction not found. "
                "You need to send a transaction first."
            )

        callbacks = await self.send_transaction_callbacks_storage.get()

        if callbacks is None:
            raise RetrySendTransactionError(
                "No callbacks found for send transaction. "
                "You need to send a transaction first."
            )

        await self.send_transaction(transaction, callbacks)

    async def _connect_wallet_proof_wrong(self) -> None:
        """
        Handle the connect wallet proof wrong.
        """
        text = self.__text_message.get("connect_wallet_proof_wrong")
        reply_markup = self.__inline_keyboard.connect_wallet_proof_wrong()

        await self._send_message(text=text, reply_markup=reply_markup)
        await self.state.set_state(TcState.connect_wallet_proof_wrong)

    async def _connect_wallet_timeout(self) -> None:
        """
        Handle the connect wallet timeout.
        """
        text = self.__text_message.get("connect_wallet_timeout")
        reply_markup = self.__inline_keyboard.send_transaction_timeout()

        await self._send_message(text=text, reply_markup=reply_markup)
        await self.state.set_state(TcState.connect_wallet_timeout)

    async def _send_transaction_timeout(self) -> None:
        """
        Handle the send transaction timeout.
        """
        text = self.__text_message.get("send_transaction_timeout")
        reply_markup = self.__inline_keyboard.send_transaction_timeout()

        await self._send_message(text=text, reply_markup=reply_markup)
        await self.state.set_state(TcState.send_transaction_timeout)

    async def _send_transaction_rejected(self) -> None:
        """
        Handle the send transaction rejection.
        """
        text = self.__text_message.get("send_transaction_rejected")
        reply_markup = self.__inline_keyboard.send_transaction_rejected()

        await self._send_message(text=text, reply_markup=reply_markup)
        await self.state.set_state(TcState.send_transaction_rejected)

    async def _send_photo(
            self,
            photo: Any,
            caption: Optional[str] = None,
            reply_markup: Optional[InlineKeyboardMarkup] = None,
    ) -> Message:
        """
        Send a photo to the user.

        :param photo: The photo to send.
        :param caption: The caption for the photo.
        :param reply_markup: Optional InlineKeyboardMarkup for the message.
        :return: Sent Message object.
        :raises TelegramBadRequest: If there is an issue with sending the photo.
        """
        message = await self.bot.send_photo(
            chat_id=self.user.id,
            photo=photo,
            caption=caption,
            reply_markup=reply_markup,
        )
        await self._delete_previous_message()
        await self.state.update_data(message_id=message.message_id)
        return message

    async def _send_message(
            self,
            text: str,
            reply_markup: Optional[InlineKeyboardMarkup] = None,
    ) -> Message:
        """
        Send or edit a message to the user.

        This method attempts to edit the existing message identified by the stored message ID. If editing is not
        possible (e.g., due to a message not found error), it sends a new message and deletes the previous one.

        :param text: The text content of the message.
        :param reply_markup: Optional InlineKeyboardMarkup for the message.
        :return: The edited or sent Message object.
        :raises TelegramBadRequest: If there is an issue with sending or editing the message.
        """
        state_data = await self.state.get_data()
        message_id = state_data.get("message_id", None)

        try:
            message = await self.bot.edit_message_text(
                text=text,
                chat_id=self.user.id,
                message_id=message_id,
                reply_markup=reply_markup,
            )
        except TelegramBadRequest as ex:
            if not any(e in ex.message for e in MESSAGE_EDIT_ERRORS):
                raise ex
            message = await self.bot.send_message(
                text=text,
                chat_id=self.state.key.chat_id,
                reply_markup=reply_markup,
            )
            await self._delete_previous_message()
        await self.state.update_data(message_id=message.message_id)

        return message

    async def _delete_previous_message(self) -> Union[Message, None]:
        """
        Delete the previous message.

        This method attempts to delete the previous message identified by the stored message ID. If deletion is not
        possible (e.g., due to a message not found error), it attempts to edit the previous message with a placeholder
        emoji. If editing is also not possible, it raises TelegramBadRequest with the appropriate error message.

        :return: The edited Message object or None if no previous message was found.
        :raises TelegramBadRequest: If there is an issue with deleting or editing the previous message.
        """
        state_data = await self.state.get_data()

        message_id = state_data.get("message_id")
        if not message_id: return  # noqa:E701

        try:
            await self.bot.delete_message(
                message_id=message_id,
                chat_id=self.user.id,
            )
        except TelegramBadRequest as ex:
            if any(e in ex.message for e in MESSAGE_DELETE_ERRORS):
                try:
                    text = self.__text_message.get("outdated_text")
                    return await self.bot.edit_message_text(
                        message_id=message_id,
                        chat_id=self.user.id,
                        text=text,
                    )
                except TelegramBadRequest as ex:
                    if not any(e in ex.message for e in MESSAGE_EDIT_ERRORS):
                        raise ex

    async def __wait_connect_wallet_task(self) -> None:
        """
        Wait for the connect wallet task.

        This method checks the AiogramTonConnect connection status periodically for up to 3 minutes (360 iterations).
        If the connection is restored, it updates the account wallet details, executes the appropriate callbacks,
        and removes the task from the task storage. If the connection is not restored within the timeout, it
        triggers the connect wallet timeout handling.

        :raises asyncio.CancelledError: If the task is cancelled.
        :raises Exception: Any unexpected exception during the process.
        """
        try:
            for _ in range(1, 361):
                await asyncio.sleep(.5)
                if self.tonconnect.connected:
                    state_data = await self.state.get_data()

                    account_wallet = AccountWallet(
                        address=Address(hex_address=self.tonconnect.account.address),
                        state_init=self.tonconnect.account.wallet_state_init,
                        public_key=self.tonconnect.account.public_key,
                        chain=self.tonconnect.account.chain,
                    )
                    info_wallet = InfoWallet.from_pytonconnect_wallet(self.tonconnect.wallet)
                    app_wallet = AppWallet(**state_data.get("app_wallet"))

                    await self.state.update_data(
                        account_wallet=account_wallet.model_dump(),
                        info_wallet=info_wallet.model_dump(),
                    )

                    if state_data.get("check_proof", False):
                        proof_payload = state_data.get("proof_payload")
                        if not check_payload(proof_payload, info_wallet):
                            await self._connect_wallet_proof_wrong()
                            break

                    self.middleware_data["account_wallet"] = account_wallet
                    self.middleware_data["info_wallet"] = info_wallet
                    self.middleware_data["app_wallet"] = app_wallet

                    callbacks = await self.connect_wallet_callbacks_storage.get()
                    await callbacks.after_callback(**self.middleware_data)
                    break
            else:
                await self._connect_wallet_timeout()

        except asyncio.CancelledError:
            pass
        except Exception:
            raise
        finally:
            self.task_storage.remove()
        return

    async def __wait_send_transaction_task(self) -> None:
        """
        Wait for the send transaction task.

        This method waits for the Tonconnect to send a transaction within a timeout of 5 minutes. If the transaction
        is sent successfully, it updates the user's last transaction details, executes the appropriate callbacks, and
        removes the task from the task storage. If the user rejects the transaction, it triggers the send transaction
        rejection handling. If the transaction is not sent within the timeout, it triggers the send transaction
        timeout handling.

        :raises UserRejectsError: If the user rejects the transaction.
        :raises asyncio.TimeoutError: If the transaction is not sent within the timeout.
        :raises asyncio.CancelledError: If the task is cancelled.
        :raises Exception: Any unexpected exception during the process.
        """
        try:
            await self.tonconnect.restore_connection()
            await self.tonconnect.unpause_connection()

            data = await self.state.get_data()
            transaction = data.get("transaction")

            result = await asyncio.wait_for(
                self.tonconnect.send_transaction(transaction=transaction),
                timeout=300,
            )
            if result:
                last_transaction_boc = result.get("boc")
                self.user.last_transaction_boc = last_transaction_boc
                await self.state.update_data(last_transaction_boc=last_transaction_boc)

                callbacks = await self.send_transaction_callbacks_storage.get()
                self.middleware_data["boc"] = last_transaction_boc
                await callbacks.after_callback(**self.middleware_data)

        except UserRejectsError:
            current_state = await self.state.get_state()

            if current_state != TcState.send_transaction.state:
                return None
            await self._send_transaction_rejected()

        except asyncio.TimeoutError:
            current_state = await self.state.get_state()

            if current_state != TcState.send_transaction.state:
                return None
            await self._send_transaction_timeout()

        except asyncio.CancelledError:
            pass
        except Exception:
            raise
        finally:
            self.tonconnect.pause_connection()
            self.task_storage.remove()
        return
