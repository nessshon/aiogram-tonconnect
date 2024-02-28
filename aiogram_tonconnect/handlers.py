from contextlib import suppress

from aiogram import Dispatcher, Router, F
from aiogram.enums import ChatType
from aiogram.types import CallbackQuery
from pytonconnect.exceptions import WalletNotConnectedError

from .manager import ATCManager
from .utils.states import TcState


class AiogramTonConnectHandlers:

    @staticmethod
    async def connect_wallet_callback_query_handler(
            call: CallbackQuery,
            atc_manager: ATCManager,
    ) -> None:
        """
        Handle callback queries related to connecting a wallet.

        :param call: The CallbackQuery instance.
        :param atc_manager: An instance of ATCManager.
        """
        atc_manager.task_storage.remove()

        if atc_manager.tonconnect.connected:
            with suppress(WalletNotConnectedError):
                await atc_manager.tonconnect.disconnect()

        if call.data.startswith("app_wallet:"):
            wallets = await atc_manager.tonconnect.get_wallets()
            app_wallet_name = call.data.split(":")[1]
            app_wallet = next((w for w in wallets if w.app_name == app_wallet_name), wallets[0])
            await atc_manager.state.update_data(app_wallet=app_wallet.model_dump())
            await atc_manager.retry_connect_wallet()

        elif call.data == "back":
            callbacks = await atc_manager.connect_wallet_callbacks_storage.get()
            await callbacks.before_callback(**atc_manager.middleware_data)

        await call.answer()

    @staticmethod
    async def connect_wallet_proof_wrong_callback_query_handler(
            call: CallbackQuery,
            atc_manager: ATCManager,
    ) -> None:
        """
        Handle callback queries related to wrong proof during wallet connection.

        :param call: The CallbackQuery instance.
        :param atc_manager: An instance of ATCManager.
        """
        if call.data == "retry":
            await atc_manager.retry_connect_wallet()
        elif call.data == "back":
            callbacks = await atc_manager.connect_wallet_callbacks_storage.get()
            await callbacks.before_callback(**atc_manager.middleware_data)

        await call.answer()

    @staticmethod
    async def connect_wallet_timeout_callback_query_handler(
            call: CallbackQuery,
            atc_manager: ATCManager,
    ) -> None:
        """
        Handle callback queries related to connection timeout during wallet connection.

        :param call: The CallbackQuery instance.
        :param atc_manager: An instance of ATCManager.
        """
        if call.data == "retry":
            await atc_manager.retry_connect_wallet()
        elif call.data == "back":
            callbacks = await atc_manager.connect_wallet_callbacks_storage.get()
            await callbacks.before_callback(**atc_manager.middleware_data)

        await call.answer()

    @staticmethod
    async def send_transaction_callback_query_handler(
            call: CallbackQuery,
            atc_manager: ATCManager,
    ) -> None:
        """
        Handle callback queries related to sending a transaction.

        :param call: The CallbackQuery instance.
        :param atc_manager: An instance of ATCManager.
        """
        atc_manager.task_storage.remove()

        if call.data == "back":
            callbacks = await atc_manager.send_transaction_callbacks_storage.get()
            atc_manager.middleware_data["account_wallet"] = atc_manager.user.account_wallet
            await callbacks.before_callback(**atc_manager.middleware_data)

        await call.answer()

    @staticmethod
    async def send_transaction_timeout_callback_query_handler(
            call: CallbackQuery,
            atc_manager: ATCManager,
    ) -> None:
        """
        Handle callback queries related to transaction timeout during sending.

        :param call: The CallbackQuery instance.
        :param atc_manager: An instance of ATCManager.
        """
        if call.data == "retry":
            await atc_manager.retry_last_send_transaction()
        elif call.data == "back":
            callbacks = await atc_manager.send_transaction_callbacks_storage.get()
            atc_manager.middleware_data["account_wallet"] = atc_manager.user.account_wallet
            await callbacks.before_callback(**atc_manager.middleware_data)

        await call.answer()

    @staticmethod
    async def send_transaction_rejected_callback_query_handler(
            call: CallbackQuery,
            atc_manager: ATCManager,
    ) -> None:
        """
        Handle callback queries related to rejected transactions.

        :param call: The CallbackQuery instance.
        :param atc_manager: An instance of ATCManager.
        """
        if call.data == "retry":
            await atc_manager.retry_last_send_transaction()
        elif call.data == "back":
            callbacks = await atc_manager.send_transaction_callbacks_storage.get()
            atc_manager.middleware_data["account_wallet"] = atc_manager.user.account_wallet
            await callbacks.before_callback(**atc_manager.middleware_data)

        await call.answer()

    def register(self, dp: Dispatcher):
        """
        Register AiogramTonConnect-related handlers with the given Dispatcher.

        :param dp: The Dispatcher instance.
        """
        router = Router()
        router.callback_query.filter(F.message.chat.type == ChatType.PRIVATE)

        router.callback_query.register(
            self.connect_wallet_callback_query_handler,
            TcState.connect_wallet,
        )
        router.callback_query.register(
            self.connect_wallet_proof_wrong_callback_query_handler,
            TcState.connect_wallet_proof_wrong,
        )
        router.callback_query.register(
            self.connect_wallet_timeout_callback_query_handler,
            TcState.connect_wallet_timeout,
        )
        router.callback_query.register(
            self.send_transaction_callback_query_handler,
            TcState.send_transaction,
        )
        router.callback_query.register(
            self.send_transaction_timeout_callback_query_handler,
            TcState.send_transaction_timeout,
        )
        router.callback_query.register(
            self.send_transaction_rejected_callback_query_handler,
            TcState.send_transaction_rejected,
        )
        dp.include_router(router)
