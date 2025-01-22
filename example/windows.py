from contextlib import suppress

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton as Button
from aiogram.types import InlineKeyboardMarkup as Markup
from aiogram.types import User
from aiogram.utils import markdown

from aiogram_tonconnect import ATCManager


class UserState(StatesGroup):
    """
    States for handling user interactions.
    """
    select_language = State()   # State for selecting the language
    main_menu = State()         # State for displaying the main menu
    send_amount_ton = State()   # State for entering the TON amount
    transaction_info = State()  # State for showing transaction details


async def delete_last_message(bot: Bot, state: FSMContext, chat_id: int, message_id: int) -> None:
    """
    Delete the last message sent to the user to keep the chat clean.
    """
    state_data = await state.get_data()
    last_message_id = state_data.get("message_id", 0)
    with suppress(Exception):
        await bot.delete_message(message_id=last_message_id, chat_id=chat_id)
    await state.update_data(message_id=message_id)


async def select_language_window(bot: Bot, event_from_user: User, atc_manager: ATCManager) -> None:
    """
    Display the language selection window to the user.
    """
    # Generate text for the language selection prompt
    text = (
        f"Привет, {markdown.hbold(event_from_user.full_name)}!\n\n"
        "Выберите язык:" if atc_manager.user.language_code == "ru" else
        f"Hello, {markdown.hbold(event_from_user.full_name)}!\n\n"
        f"Select language:"
    )

    # Create an inline keyboard with language options
    reply_markup = Markup(inline_keyboard=[
        [
            Button(text="Русский", callback_data="ru"),
            Button(text="English", callback_data="en")
        ]
    ])

    # Send the message and update the user's FSM state
    message = await bot.send_message(event_from_user.id, text, reply_markup=reply_markup)
    await delete_last_message(bot, atc_manager.state, atc_manager.user.id, message.message_id)
    await atc_manager.state.set_state(UserState.select_language)


async def main_menu_window(bot: Bot, atc_manager: ATCManager) -> None:
    """
    Display the main menu window to the user.
    """
    # Generate text with information about the connected wallet
    text = (
        f"Подключенный кошелек {atc_manager.connector.wallet_app.name}:\n\n"
        f"{markdown.hcode(atc_manager.connector.account.address.to_str(is_bounceable=False))}"
        if atc_manager.user.language_code == "ru" else
        f"Connected wallet {atc_manager.connector.wallet_app.name}:\n\n"
        f"{markdown.hcode(atc_manager.connector.account.address.to_str(is_bounceable=False))}"
    )

    # Create an inline keyboard with options to send TON or disconnect
    send_amount_ton_text = "Отправить TON" if atc_manager.user.language_code == "ru" else "Send TON"
    disconnect_text = "Отключиться" if atc_manager.user.language_code == "ru" else "Disconnect"
    reply_markup = Markup(inline_keyboard=[
        [Button(text=send_amount_ton_text, callback_data="send_amount_ton")],
        [Button(text=disconnect_text, callback_data="disconnect")]
    ])

    message = await bot.send_message(atc_manager.user.id, text, reply_markup=reply_markup)
    await delete_last_message(bot, atc_manager.state, atc_manager.user.id, message.message_id)
    await atc_manager.state.set_state(UserState.main_menu)


async def send_amount_ton_window(bot: Bot, atc_manager: ATCManager) -> None:
    """
    Display the window for entering the amount of TON to send.
    """
    # Generate text asking the user to input the TON amount
    text = (
        "Сколько TON вы хотите отправить?"
        if atc_manager.user.language_code == "ru" else
        "How much TON do you want to send?"
    )

    # Create a button to go back to the main menu
    button_text = "‹ Назад" if atc_manager.user.language_code == "ru" else "‹ Back"
    reply_markup = Markup(inline_keyboard=[
        [Button(text=button_text, callback_data="back")]
    ])

    # Send the message and update the user's FSM state
    message = await bot.send_message(atc_manager.user.id, text, reply_markup=reply_markup)
    await delete_last_message(bot, atc_manager.state, atc_manager.user.id, message.message_id)
    await atc_manager.state.set_state(UserState.send_amount_ton)


async def transaction_info_windows(bot: Bot, atc_manager: ATCManager, boc: str) -> None:
    """
    Display the transaction information to the user.
    """
    # Generate text showing transaction details
    text = (
        "Транзакция успешно отправлена!\n\n"
        f"boc:\n{boc}" if atc_manager.user.language_code == "ru" else
        "Transaction successfully sent!\n\n"
        f"boc:\n{boc}"
    )

    # Create a button to navigate back to the main menu
    button_text = "‹ На главную" if atc_manager.user.language_code == "ru" else "‹ Go to main"
    reply_markup = Markup(inline_keyboard=[
        [Button(text=button_text, callback_data="go_to_main")]
    ])

    # Send the message and update the user's FSM state
    message = await bot.send_message(atc_manager.user.id, text, reply_markup=reply_markup)
    await delete_last_message(bot, atc_manager.state, atc_manager.user.id, message.message_id)
    await atc_manager.state.set_state(UserState.transaction_info)
