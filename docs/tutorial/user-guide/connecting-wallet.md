## Introduction

**Description:**

- **ATCMager:**
  The main control class is which is responsible for managing the transition of windows, connecting a
  wallet and sending transactions.

- **open_connect_wallet_window:**
  The main method of the ATCManager class, used to present the wallet connection window to users.

- **ConnectWalletCallbacks:**
  The core set of callbacks required by the open_connect_wallet_window method. It plays a decisive role in circulation
  actions during and after the wallet connection process.

- **before_callback:**
  The callback function in ConnectWalletCallbacks is triggered when users click the back button in the wallet
  connection window.

- **after_callback:**
  A callback function in ConnectWalletCallbacks that is executed after a successful connection to the wallet. He
  transmits comprehensive information for processors.

The ATCManager class is automatically distributed to all handlers as an atc_manager object via middleware.
The `open_connect_wallet_window` method, requiring one argument, ConnectWalletCallbacks acts as a gateway to present the
wallet connection window. This set of callbacks, consisting of `before_callback` and `after_callback`.

**Callback examples:**

In our example, two callback functions will be created: `select_language_window` and `main_menu_window`.

- **before_callback:** `select_language_window`
  This callback is used when the Start button is clicked or the /start command is entered to prompt the user for a
  language choice.

- **after_callback:** `main_menu_window`
  This callback is the main menu that displays information about the connected wallet address and the one being used
  wallet. In addition, there is a button to disable the wallet.

---

## Writing windows

This section defines window functions for callbacks and user state.
Open the `windows.py` file and insert the following code:

### User State

```python title="windows.py"
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import User
from aiogram.types import InlineKeyboardButton as Button, User
from aiogram.types import InlineKeyboardMarkup as Markup
from aiogram.utils import markdown

from aiogram_tonconnect import ATCManager
from aiogram_tonconnect.tonconnect.models import AccountWallet, AppWallet


# Define a state group for the user with two states
class UserState(StatesGroup):
    select_language = State()
    main_menu = State()
```

In this section, a custom UserState class is defined, which extends the StatesGroup class from the aiogram.fsm.state
module. It represents different states that the user can be in.

### Select language window

```python title="windows.py"
async def select_language_window(event_from_user: User, atc_manager: ATCManager, **_) -> None:
    """
    Displays the language selection window.

   :param event_from_user: Telegram user object from middleware.
   :param atc_manager: ATCManager instance for managing TON Connect integration.
   :param_: Unused data from the middleware.
   :return: No
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
```

This function represents the window for selecting the language. It generates appropriate text based on the user's
language and creates an inline keyboard for language selection.

### Main menu window

```python title="windows.py"
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
```

This function represents the main menu window. It generates text with information about the connected wallet and creates
an inline keyboard with a disconnect option.

---

## Writing Handlers

In this section, handlers for commands and callback queries are defined.
Open the `handlers.py` file and insert the following code:

### Router Configuration

```python title="handlers.py"
from contextlib import suppress

from aiogram import Router, F
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from pytonconnect.exceptions import WalletNotConnectedError

from aiogram_tonconnect import ATCManager
from aiogram_tonconnect.tonconnect.models import ConnectWalletCallbacks

from .windows import UserState, select_language_window, main_menu_window

# Router Configuration
router = Router()
router.message.filter(F.chat.type == ChatType.PRIVATE)
router.callback_query.filter(F.message.chat.type == ChatType.PRIVATE)
```

The router is configured to filter messages and callback queries only from private chats.

### Start Command Handler

```python title="handlers.py"
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
```

This handler is triggered when a user sends the /start command. It initiates the language selection window.

### Select Language Handler

```python title="handlers.py"
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

    await call.answer()
```

This handler is triggered when a user selects a language. It updates the language and opens the connect wallet window.

### Main Menu Handler

```python title="handlers.py"
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

    await call.answer()
```

This handler is triggered when a user interacts with the main menu. It handles disconnecting and opening the connect
wallet window.

### Running the Bot

To run the Bot, use the following command in your terminal:

```bash
python -m bot
```

The bot source code is available
on [GitHub](https://github.com/nessshon/aiogram-tonconnect/blob/main/example/connecting-wallet/).
