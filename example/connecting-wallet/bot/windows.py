from aiogram.fsm.state import StatesGroup, State
from aiogram.types import User
from aiogram.types import InlineKeyboardButton as Button
from aiogram.types import InlineKeyboardMarkup as Markup
from aiogram.utils import markdown

from aiogram_tonconnect import ATCManager
from aiogram_tonconnect.tonconnect.models import AccountWallet, AppWallet


# Define a state group for the user with two states
class UserState(StatesGroup):
    select_language = State()
    main_menu = State()


async def select_language_window(event_from_user: User, atc_manager: ATCManager, **_) -> None:
    """
    Displays the language selection window.

   :param event_from_user: Telegram user object from middleware.
   :param atc_manager: ATCManager instance for managing TON Connect integration.
   :param_: Unused data from the middleware.
   :return: None
    """
    # Code for generating text based on the user's language
    text = (
        f"Привет, {markdown.hbold(event_from_user.full_name)}!\n\n"
        "Выберите язык:"
        if atc_manager.user.language_code == "ru" else
        f"Hello, {markdown.hbold(event_from_user.full_name)}!\n\n"
        f"Select language:"
    )

    # Code for creating inline keyboard with language options
    reply_markup = Markup(inline_keyboard=[
        [Button(text="Русский", callback_data="ru"),
         Button(text="English", callback_data="en")]
    ])

    # Sending the message and updating user state
    await atc_manager.send_message(text, reply_markup=reply_markup)
    await atc_manager.state.set_state(UserState.select_language)


async def main_menu_window(atc_manager: ATCManager, app_wallet: AppWallet,
                           account_wallet: AccountWallet, **_) -> None:
    """
    Displays the main menu window.

    :param atc_manager: ATCManager instance for managing TON Connect integration.
    :param app_wallet: AppWallet instance representing the connected wallet application.
    :param account_wallet: AccountWallet instance representing the connected wallet account.
    :param _: Unused data from the middleware.
    :return: None
    """
    # Code for generating text with connected wallet information
    text = (
        f"Подключенный кошелек {app_wallet.name}:\n\n"
        f"{markdown.hcode(account_wallet.address)}"
        if atc_manager.user.language_code == "ru" else
        f"Connected wallet {app_wallet.name}:\n\n"
        f"{markdown.hcode(account_wallet.address)}"
    )

    # Code for creating inline keyboard with disconnect option
    button_text = "Отключиться" if atc_manager.user.language_code == "ru" else "Disconnect"
    reply_markup = Markup(inline_keyboard=[
        [Button(text=button_text, callback_data="disconnect")],
    ])

    # Sending the message and updating user state
    await atc_manager.send_message(text, reply_markup=reply_markup)
    await atc_manager.state.set_state(UserState.main_menu)
