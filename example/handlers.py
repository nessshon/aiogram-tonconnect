from typing import Union

from aiogram import Router, F
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from tonutils.tonconnect.models import Transaction

from aiogram_tonconnect import ATCManager
from aiogram_tonconnect.tonconnect.models import (
    ConnectWalletCallbacks,
    SendTransactionCallbacks,
)
from windows import (
    UserState,
    main_menu_window,
    select_language_window,
    send_amount_ton_window,
    transaction_info_windows,
)

# Router for managing private chat interactions
router = Router()
router.message.filter(F.chat.type == ChatType.PRIVATE)
router.callback_query.filter(F.message.chat.type == ChatType.PRIVATE)


@router.message(Command("start"))
async def start_command(message: Message, atc_manager: ATCManager) -> None:
    """
    Handler for the /start command.
    Initiates the language selection process.
    """
    if atc_manager.connector.connected:
        await main_menu_window(message.bot, atc_manager)
    else:
        await select_language_window(message.bot, message.from_user, atc_manager)
    await message.delete()


@router.callback_query(UserState.select_language)
async def select_language_handler(call: CallbackQuery, atc_manager: ATCManager) -> None:
    """
    Handles language selection by the user.
    Updates the interface language and proceeds to wallet connection.
    """
    if call.data in ["ru", "en"]:
        await atc_manager.update_interfaces_language(call.data)
        callbacks = ConnectWalletCallbacks(
            before_callback=select_language_window,
            after_callback=main_menu_window,
        )
        await atc_manager.connect_wallet(callbacks)
    await call.answer()


@router.callback_query(UserState.main_menu)
async def main_menu_handler(call: CallbackQuery, atc_manager: ATCManager) -> None:
    """
    Handles main menu interactions.
    Allows the user to disconnect the wallet or send TON.
    """
    if call.data == "disconnect":
        if atc_manager.connector.connected:
            await atc_manager.connector.disconnect_wallet()
        callbacks = ConnectWalletCallbacks(
            before_callback=select_language_window,
            after_callback=main_menu_window,
        )
        await atc_manager.connect_wallet(callbacks)
    elif call.data == "send_amount_ton":
        await send_amount_ton_window(call.bot, atc_manager)
    await call.answer()


@router.callback_query(UserState.send_amount_ton)
async def send_amount_ton_handler(call: CallbackQuery, atc_manager: ATCManager, **data) -> None:
    """
    Handles interactions related to sending TON.
    Allows the user to go back to the main menu.
    """
    if call.data == "back":
        await main_menu_window(call.bot, atc_manager)
    await call.answer()


@router.message(UserState.send_amount_ton)
async def send_amount_ton_message_handler(message: Message, atc_manager: ATCManager) -> None:
    """
    Handles input for the amount of TON to send.
    Validates the input and initiates the transaction.
    """

    def validate_amount(amount: str) -> Union[float, None]:
        try:
            return float(amount.replace(",", "."))
        except ValueError:
            return None

    amount_ton = validate_amount(message.text)
    if amount_ton:
        transaction = Transaction(
            messages=[
                Transaction.create_message(
                    destination=atc_manager.user.wallet_address,
                    amount=amount_ton,
                    body="Hello from @aiogramTONConnectBot!"
                )
            ]
        )
        callbacks = SendTransactionCallbacks(
            before_callback=send_amount_ton_window,
            after_callback=transaction_info_windows,
        )
        await atc_manager.send_transaction(callbacks=callbacks, transaction=transaction)
    await message.delete()
