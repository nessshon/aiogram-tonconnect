from __future__ import annotations

import asyncio
import inspect
import time
from contextlib import suppress
from typing import Dict, Any, Union, Optional, Callable

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    BufferedInputFile,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.utils.markdown import hide_link
from tonutils.tonconnect import (
    TonConnect,
    Connector,
)
from tonutils.tonconnect.models import (
    WalletApp,
    WalletInfo,
    Transaction,
    SendTransactionResponse,
)
from tonutils.tonconnect.utils import generate_proof_payload
from tonutils.tonconnect.utils.exceptions import (
    WalletNotConnectedError,
    RequestTimeoutError,
    UserRejectsError,
    TonConnectError,
)

from .tonconnect.callbacks import (
    ConnectWalletCallbackStorage,
    SendTransactionCallbackStorage,
)
from .tonconnect.models import (
    ATCUser,
    ConnectWalletCallbacks,
    SendTransactionCallbacks,
)
from .tonconnect.tasks import TaskStorage
from .utils.exceptions import (
    LanguageCodeNotSupported,
    RetryConnectWalletError,
    RetrySendTransactionError,
    MESSAGE_DELETE_ERRORS,
    MESSAGE_EDIT_ERRORS,
)
from .utils.keyboards import InlineKeyboardBase
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
    :param tonconnect: AiogramTonConnect instance.
    :param text_message: TextMessageBase class for managing text messages.
    :param inline_keyboard: InlineKeyboardBase class for managing inline keyboards.
    :param qrcode_provider: QRImageProviderBase or QRUrlProviderBase instance.
    :param data: Additional data.
    """

    def __init__(
            self,
            user: ATCUser,
            connector: Connector,
            tonconnect: TonConnect,
            text_message: TextMessageBase,
            inline_keyboard: InlineKeyboardBase,
            qrcode_provider: Union[QRImageProviderBase, QRUrlProviderBase],
            data: Dict[str, Any],
    ) -> None:
        self.user = user
        self.connector = connector
        self.tonconnect = tonconnect

        self.__data: Dict[str, Any] = data
        self.__text_message = text_message
        self.__inline_keyboard = inline_keyboard
        self.__qrcode_provider = qrcode_provider

        self.bot: Bot = data.get("bot")  # type: ignore
        self.state: FSMContext = data.get("state")  # type: ignore

        self.connect_wallet_callbacks = ConnectWalletCallbackStorage(
            storage=tonconnect.storage,
            user_id=user.id,
        )
        self.send_transaction_callbacks = SendTransactionCallbackStorage(
            storage=tonconnect.storage,
            user_id=user.id,
        )
        self.task_storage = TaskStorage(user_id=user.id)

    @property
    def middleware_data(self) -> Dict[str, Any]:
        """
        Get middleware data.
        """
        return self.__data

    async def __get_filtered_kwargs(self, func: Callable) -> Dict[str, Any]:
        params = inspect.signature(func).parameters
        return {k: v for k, v in self.middleware_data.items() if k in params}

    async def __execute_callback(self, storage, callback_type: str) -> None:
        """
        Generic method to execute a callback of the given type.

        :param storage: The storage containing the callback functions.
        :param callback_type: The type of callback to execute ('before_callback' or 'after_callback').
        """
        callbacks = await storage.get()
        callback = getattr(callbacks, callback_type)
        filtered_kwargs = await self.__get_filtered_kwargs(callback)
        await callback(**filtered_kwargs)

    async def execute_connect_wallet_after_callback(self) -> None:
        await self.__execute_callback(self.connect_wallet_callbacks, "after_callback")

    async def execute_connect_wallet_before_callback(self) -> None:
        await self.__execute_callback(self.connect_wallet_callbacks, "before_callback")

    async def execute_transaction_after_callback(self) -> None:
        await self.__execute_callback(self.send_transaction_callbacks, "after_callback")

    async def execute_transaction_before_callback(self) -> None:
        await self.__execute_callback(self.send_transaction_callbacks, "before_callback")

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
            check_proof: bool = True,
            proof_payload: Optional[str] = None,
            redirect_url: str = "back",
    ) -> None:
        """
        Open the connect wallet window.

        :param callbacks: Callbacks to execute.
        :param check_proof: Check proof if True.
        :param proof_payload: Payload for ton_proof.
        :param redirect_url: The URL to which the user should be redirected after connecting.

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

        await self.connect_wallet_callbacks.add(callbacks)

        state_data = await self.state.get_data()
        wallets = await self.tonconnect.get_wallets()

        app_wallet_dict = state_data.get("app_wallet") or wallets[0].to_dict()
        app_wallet = WalletApp.from_dict(app_wallet_dict)

        ton_proof = proof_payload or generate_proof_payload()
        universal_url = await self.connector.connect_wallet(
            app_wallet,
            redirect_url=redirect_url,
            ton_proof=ton_proof
        )

        await self.state.update_data(
            app_wallet=app_wallet.to_dict(),
            proof_payload=ton_proof,
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
        callbacks = await self.connect_wallet_callbacks.get()

        if callbacks is None:
            raise RetryConnectWalletError(
                "No callbacks found for connect wallet. "
                "You need a connect wallet first."
            )

        await self.connect_wallet(callbacks)

    async def _send_connect_wallet_window(
            self,
            text: str,
            reply_markup: InlineKeyboardMarkup,
            universal_url: str,
            app_wallet: WalletApp,
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
        await self.tonconnect.init_connector(self.user.id)
        with suppress(WalletNotConnectedError):
            await self.connector.disconnect_wallet()

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
        data = await self.state.get_data()
        last_rpc_request_id = data.get("rpc_request_id", 0)

        await self.tonconnect.init_connector(self.user.id)

        self.connector._prepare_transaction(transaction)  # noqa
        if self.connector.device is not None and self.connector.wallet is not None:
            self.connector.device.verify_send_transaction_feature(
                self.connector.wallet,
                len(transaction.messages),
            )

        await self.state.update_data(transaction=transaction.to_dict())
        await self.send_transaction_callbacks.add(callbacks)
        task = asyncio.create_task(self.__wait_send_transaction_task(transaction, last_rpc_request_id))
        self.task_storage.add(task)

        text = self.__text_message.get("send_transaction").format(
            wallet_name=self.connector.wallet_app.name,  # type: ignore
        )

        reply_markup = self.__inline_keyboard.send_transaction(
            self.connector.wallet_app.name, self.connector.wallet_app.direct_url,  # type: ignore
        )

        await self._send_message(text=text, reply_markup=reply_markup)
        await self.state.set_state(TcState.send_transaction)

    async def retry_last_send_transaction(self) -> None:
        data = await self.state.get_data()

        try:
            transaction = Transaction.from_dict(data.get("transaction"))  # type: ignore
            transaction.valid_until = int(time.time() + 5 * 60)
        except KeyError:
            raise RetrySendTransactionError(
                "Last transaction not found. "
                "You need to send a transaction first."
            )

        callbacks = await self.send_transaction_callbacks.get()

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

    async def _connect_wallet_reject(self) -> None:
        """
        Handle the user's request to decline the connection.
        """
        text = self.__text_message.get("connect_wallet_rejected")
        reply_markup = self.__inline_keyboard.connect_wallet_rejected()

        await self._send_message(text=text, reply_markup=reply_markup)
        await self.state.set_state(TcState.connect_wallet_rejected)

    async def _connect_wallet_timeout(self) -> None:
        """
        Handle the connect wallet timeout.
        """
        text = self.__text_message.get("connect_wallet_timeout")
        reply_markup = self.__inline_keyboard.connect_wallet_timeout()

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
    ) -> Union[Message, bool]:
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
        if isinstance(message, Message):
            await self.state.update_data(message_id=message.message_id)

        return message

    async def _delete_previous_message(self) -> Optional[Union[Message, bool]]:
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

        if message_id is not None:
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
        return None

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
            async with self.connector.connect_wallet_context() as result:
                if isinstance(result, WalletInfo):
                    state_data = await self.state.get_data()
                    if self.connector.wallet is not None and self.connector.account is not None:
                        await self.state.update_data(
                            info_wallet=self.connector.wallet.to_dict(),
                            account_wallet=self.connector.account.to_dict(),
                        )

                    if state_data.get("check_proof", False):
                        if self.connector.wallet is None:
                            raise RuntimeError("Wallet must not be None during proof verification")

                        proof_payload = state_data.get("proof_payload")
                        is_valid_proof = self.connector.wallet.verify_proof_payload(proof_payload)

                        if not is_valid_proof:
                            await self.disconnect_wallet()
                            await self._connect_wallet_proof_wrong()
                            return

                    self.middleware_data["connector"] = self.connector
                    await self.execute_connect_wallet_after_callback()

                elif isinstance(result, RequestTimeoutError):
                    await self._connect_wallet_timeout()

                elif isinstance(result, UserRejectsError):
                    await self._connect_wallet_reject()

        except asyncio.CancelledError:
            pass
        except Exception:
            raise
        finally:
            self.task_storage.remove()

    async def __wait_send_transaction_task(self, transaction: Transaction, last_rpc_request_id: int = 0) -> None:
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
            try:
                self.connector.cancel_pending_request(last_rpc_request_id)
            except TonConnectError:
                pass

            rpc_request_id = await self.connector.send_transaction(transaction)
            await self.state.update_data(rpc_request_id=rpc_request_id)

            async with self.connector.pending_request_context(rpc_request_id) as result:
                if isinstance(result, SendTransactionResponse):
                    last_transaction_boc = result.boc
                    last_normalized_hash = result.normalized_hash

                    self.__data["boc"] = last_transaction_boc
                    self.__data["normalized_hash"] = last_normalized_hash

                    self.user.last_transaction_boc = last_transaction_boc
                    self.user.last_normalized_hash = last_normalized_hash

                    await self.state.update_data(
                        last_transaction_boc=last_transaction_boc,
                        last_normalized_hash=last_normalized_hash,
                    )
                    await self.execute_transaction_after_callback()

                elif isinstance(result, RequestTimeoutError):
                    current_state = await self.state.get_state()
                    if current_state != TcState.send_transaction.state:
                        return
                    await self._send_transaction_timeout()

                elif isinstance(result, UserRejectsError):
                    current_state = await self.state.get_state()
                    if current_state != TcState.send_transaction.state:
                        return
                    await self._send_transaction_rejected()

        except asyncio.CancelledError:
            pass
        except Exception:
            raise
        finally:
            self.task_storage.remove()
