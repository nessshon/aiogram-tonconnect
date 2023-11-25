from contextlib import suppress
from typing import Union

from aiogram import Router, F
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from pytonconnect.exceptions import WalletNotConnectedError

from aiogram_tonconnect import ATCManager
from aiogram_tonconnect.tonconnect.models import ConnectWalletCallbacks, SendTransactionCallbacks
from aiogram_tonconnect.tonconnect.transactions import TONTransferTransaction

from .windows import (
    UserState,
    main_menu_window,
    select_language_window,
    send_amount_ton_window,
    transaction_info_windows,
)

# Router Configuration
router = Router()
router.message.filter(F.chat.type == ChatType.PRIVATE)
router.callback_query.filter(F.message.chat.type == ChatType.PRIVATE)


@router.message(Command("start"))
async def start_command(message: Message, atc_manager: ATCManager) -> None:
    """
    Handler for the /start command.

    :param message: The Message object representing the incoming command.
    :param atc_manager: ATCManager instance for managing TON Connect integration.
    :return: None
    """
    # Calling up the language selection window
    await select_language_window(message.from_user, atc_manager)


@router.callback_query(UserState.select_language)
async def select_language_handler(call: CallbackQuery, atc_manager: ATCManager) -> None:
    """
    Handler for language selection callback.

    :param call: The CallbackQuery object representing the callback.
    :param atc_manager: ATCManager instance for managing TON Connect integration.
    :return: None
    """
    # Check if the call data is in supported languages:
    if call.data in ["ru", "en"]:
        # Updating the language in the aiogram-tonconnect interface
        await atc_manager.update_interfaces_language(call.data)

        # Create ConnectWalletCallbacks object
        # with before_callback and after_callback functions
        callbacks = ConnectWalletCallbacks(
            before_callback=select_language_window,
            after_callback=main_menu_window,
        )
        # Open the connect wallet window using the ATCManager instance
        # and the specified callbacks
        await atc_manager.open_connect_wallet_window(callbacks)

    # Acknowledge the callback query
    await call.answer()


@router.callback_query(UserState.main_menu)
async def main_menu_handler(call: CallbackQuery, atc_manager: ATCManager) -> None:
    """
    Handler for the main menu callback.

    :param call: The CallbackQuery object representing the callback.
    :param atc_manager: ATCManager instance for managing TON Connect integration.
    :return: None
    """
    # Check if the user clicked the "disconnect" button
    if call.data == "disconnect":
        # Check if wallet is connected before attempting to disconnect
        if atc_manager.tonconnect.connected:
            with suppress(WalletNotConnectedError):
                # Disconnect from the wallet with suppress
                # to handle WalletNotConnectedError
                await atc_manager.tonconnect.disconnect()

        # Create ConnectWalletCallbacks object with before_callback
        # and after_callback functions
        callbacks = ConnectWalletCallbacks(
            before_callback=select_language_window,
            after_callback=main_menu_window,
        )

        # Open the connect wallet window using the ATCManager instance
        # and the specified callbacks
        await atc_manager.open_connect_wallet_window(callbacks)

    elif call.data == "send_amount_ton":
        await send_amount_ton_window(atc_manager)

    # Acknowledge the callback query
    await call.answer()


@router.callback_query(UserState.send_amount_ton)
async def send_amount_ton_handler(call: CallbackQuery, atc_manager: ATCManager, **data) -> None:
    """
    Handler for the send amount TON callback.

    :param call: The CallbackQuery object representing the callback.
    :param atc_manager: ATCManager instance for managing TON Connect integration.
    :return: None
    """
    # Check if the "back" button is pressed
    if call.data == "back":
        # Navigate back to the main menu
        await main_menu_window(atc_manager, **data)

    # Acknowledge the callback query
    await call.answer()


@router.message(UserState.send_amount_ton)
async def send_amount_ton_message_handler(message: Message, atc_manager: ATCManager) -> None:
    """
    Handler for sending the TON amount.

    :param message: The Message object representing the incoming message.
    :param atc_manager: ATCManager instance for managing TON Connect integration.
    :return: None
    """
    # Check if the message content type is text
    if message.content_type == "text":
        # Validate the entered amount as a float
        def validate_amount(amount: str) -> Union[float, None]:
            try:
                amount = float(amount.replace(',', '.'))
            except ValueError:
                return None
            return amount

        # Get the validated amount
        amount_ton = validate_amount(message.text)
        # If the amount is valid, create a TONTransferTransaction
        if amount_ton:
            transaction = TONTransferTransaction(
                address=atc_manager.user.account_wallet.address,
                amount=amount_ton,
                comment="Hello from @aiogramTONConnectBot!"
            )
            # Set up callbacks for the transaction
            callbacks = SendTransactionCallbacks(
                before_callback=send_amount_ton_window,
                after_callback=transaction_info_windows,
            )
            # Open the window for sending the transaction using the ATCManager instance
            await atc_manager.open_send_transaction_window(
                callbacks=callbacks,
                transaction=transaction,
            )

    # Delete the original message containing the amount input
    await message.delete()


@router.callback_query(UserState.transaction_info)
async def transaction_info_handler(call: CallbackQuery, atc_manager: ATCManager, **data) -> None:
    """
    Handler for the transaction information callback.

    :param call: The CallbackQuery object representing the callback.
    :param atc_manager: ATCManager instance for managing TON Connect integration.
    :return: None
    """
    # Check if the "go_to_main" button is pressed
    if call.data == "go_to_main":
        # Navigate back to the main menu
        await main_menu_window(atc_manager, **data)

    # Acknowledge the callback query
    await call.answer()
