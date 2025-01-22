from contextlib import suppress

from aiogram import Dispatcher, Router, F
from aiogram.enums import ChatType
from aiogram.types import CallbackQuery
from tonutils.tonconnect.utils.exceptions import WalletNotConnectedError

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
        await atc_manager.tonconnect.init_connector(atc_manager.user.id)
        atc_manager.task_storage.remove()

        if atc_manager.connector.connected:
            with suppress(WalletNotConnectedError):
                await atc_manager.connector.disconnect_wallet()

        if call.data and call.data.startswith("app_wallet:"):
            wallets = await atc_manager.tonconnect.get_wallets()
            app_wallet_name = call.data.split(":")[1]
            app_wallet = next((w for w in wallets if w.app_name == app_wallet_name), wallets[0])
            await atc_manager.state.update_data(app_wallet=app_wallet.to_dict())
            await atc_manager.retry_connect_wallet()

        elif call.data == "back":
            atc_manager.connector.cancel_connection_request()
            await atc_manager.connector.bridge.close()
            await atc_manager.execute_connect_wallet_before_callback()

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
        await atc_manager.tonconnect.init_connector(atc_manager.user.id)

        if call.data == "retry":
            await atc_manager.retry_connect_wallet()
        elif call.data == "back":
            await atc_manager.execute_connect_wallet_before_callback()

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
        await atc_manager.tonconnect.init_connector(atc_manager.user.id)

        if call.data == "retry":
            await atc_manager.retry_connect_wallet()
        elif call.data == "back":
            await atc_manager.execute_connect_wallet_before_callback()

        await call.answer()

    @staticmethod
    async def connect_wallet_rejected_callback_query_handler(
            call: CallbackQuery,
            atc_manager: ATCManager,
    ) -> None:
        """
        Handle callback queries related to wallet connection rejection.

        :param call: The CallbackQuery instance.
        :param atc_manager: An instance of ATCManager.
        """
        await atc_manager.tonconnect.init_connector(atc_manager.user.id)

        if call.data == "retry":
            await atc_manager.retry_connect_wallet()
        elif call.data == "back":
            await atc_manager.execute_connect_wallet_before_callback()

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
        await atc_manager.tonconnect.init_connector(atc_manager.user.id)

        atc_manager.task_storage.remove()

        if call.data == "back":
            state_data = await atc_manager.state.get_data()
            last_rpc_request_id = state_data.get("last_rpc_request_id", 0)
            atc_manager.connector.cancel_pending_transaction(last_rpc_request_id)
            await atc_manager.execute_transaction_before_callback()

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
        await atc_manager.tonconnect.init_connector(atc_manager.user.id)

        if call.data == "retry":
            await atc_manager.retry_last_send_transaction()
        elif call.data == "back":
            await atc_manager.execute_transaction_before_callback()

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
        await atc_manager.tonconnect.init_connector(atc_manager.user.id)

        if call.data == "retry":
            await atc_manager.retry_last_send_transaction()
        elif call.data == "back":
            await atc_manager.execute_transaction_before_callback()

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
            self.connect_wallet_timeout_callback_query_handler,
            TcState.connect_wallet_rejected,
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
