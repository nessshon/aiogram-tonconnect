from aiogram import Router, F
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from aiogram_tonconnect import ATCManager
from aiogram_tonconnect.tonconnect.models import ConnectWalletCallbacks

from .windows import UserState, select_language_window, main_menu_window

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
        await atc_manager.connect_wallet(callbacks)

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
            # Disconnect from the wallet
            await atc_manager.disconnect_wallet()

        # Create ConnectWalletCallbacks object with before_callback
        # and after_callback functions
        callbacks = ConnectWalletCallbacks(
            before_callback=select_language_window,
            after_callback=main_menu_window,
        )

        # Open the connect wallet window using the ATCManager instance
        # and the specified callbacks
        await atc_manager.connect_wallet(callbacks)

    # Acknowledge the callback query
    await call.answer()
