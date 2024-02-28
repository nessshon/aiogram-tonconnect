# Introduction

In this example, we will use the previous code and add new functionality to it for sending a transaction request to the
wallet.

### Description

- **send_transaction:**
  The main method of the ATCManager class, used to present users with a window for sending and confirming a transaction.

- **SendTransactionCallbacks:**
  The core set of callbacks required by the `send_transaction` method. It plays a decisive role in
  circulation actions during sending and after confirmation of the transaction.

### Callback Examples

In our example, two new callback functions will be created: `send_amount_ton_window` and `transaction_info_windows`.

- **before_callback:** `send_amount_ton_window`
  This callback is used when the "Submit Transaction" button is clicked to prompt the user to enter the amount of TON to
  send to the wallet.

- **after_callback:** `transaction_info_windows`
  This callback is a window that displays information about the submitted transaction. It will also have a button to go
  to the main menu.

---

### Writing Windows

This section defines window functions for callbacks and user state.Let's add two new states to it. Open the `windows.py`
file and insert the following
code:

#### User State

```python title="windows.py"
from aiogram.fsm.state import StatesGroup, State
from aiogram_tonconnect import ATCManager
from aiogram_tonconnect.tonconnect.models import AccountWallet, AppWallet


# Define a state group for the user with two states
class UserState(StatesGroup):
    select_language = State()
    main_menu = State()
    send_amount_ton = State()  # new
    transaction_info = State()  # new
```

In this section, a custom UserState class is defined, which extends the StatesGroup class from the aiogram.fsm.state
module. It represents different states that the user can be in.

#### Send Amount TON Window

```python title="windows.py"
async def send_amount_ton_window(atc_manager: ATCManager, **_) -> None:
    """
    Displays the window for sending TON.

    :param atc_manager: ATCManager instance for managing TON Connect integration.
    :param _: Unused data from the middleware.
    :return: None
    """
    # Determine text based on user's language
    text = (
        "How much TON do you want to send?"
        if atc_manager.user.language_code == "en" else
        "Сколько TON вы хотите отправить?"
    )
    button_text = "‹ Back" if atc_manager.user.language_code == "en" else "‹ Назад"
    reply_markup = Markup(inline_keyboard=[
        [Button(text=button_text, callback_data="back")]
    ])

    # Send the message and update user state
    await atc_manager._send_message(text, reply_markup=reply_markup)
    await atc_manager.state.set_state(UserState.send_amount_ton)
```

This function represents the window for sending the TON amount. It generates text based on the user's language and
creates an inline keyboard for navigation.

#### Transaction Info Window

```python title="windows.py"
async def transaction_info_windows(atc_manager: ATCManager, boc: str, **_) -> None:
    """
    Displays the transaction information window.

    :param atc_manager: ATCManager instance for managing TON Connect integration.
    :param boc: The BOC (Bag of Cells) representing the transaction.
    :param _: Unused data from the middleware.
    :return: None
    """
    # Determine text based on user's language and show transaction details
    text = (
        "Transaction successfully sent!\n\n"
        f"boc:\n{boc}"
        if atc_manager.user.language_code == "en" else
        "Транзакция успешно отправлена!\n\n"
        f"boc:\n{boc}"
    )
    button_text = "‹ Go to main" if atc_manager.user.language_code == "en" else "‹ На главную"
    reply_markup = Markup(inline_keyboard=[
        [Button(text=button_text, callback_data="go_to_main")]
    ])

    # Send the message and update user state
    await atc_manager._send_message(text, reply_markup=reply_markup)
    await atc_manager.state.set_state(UserState.transaction_info)
```

This function represents the transaction information window. It generates text based on the user's language and includes
transaction details with an option to go back to the main menu.

### Writing Handlers

This section defines command and callback request handlers. We need to modify the main menu handler to process the “send
transaction” button and add new handlers. Open the handlers.py file and paste the following code:

#### Router Configuration

```python title="handlers.py"
from contextlib import suppress
from aiogram import Router, F
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from pytonconnect.exceptions import WalletNotConnectedError

from aiogram_tonconnect import ATCManager
from aiogram_tonconnect.tonconnect.models import (
    ConnectWalletCallbacks,
    SendTransactionCallbacks,  # new
)

from .windows import (
    UserState,
    main_menu_window,
    select_language_window,
    send_amount_ton_window,  # new
    transaction_info_windows,  # new
)

# Router Configuration
router = Router()
router.message.filter(F.chat.type == ChatType.PRIVATE)
router.callback_query.filter(F.message.chat.type == ChatType.PRIVATE)
```

The router is configured to filter messages and callback queries only from private chats.

#### Main Menu Handler

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

    elif call.data == "send_amount_ton":
        await send_amount_ton_window(atc_manager)

    # Acknowledge the callback query
    await call.answer()
```

This handler fires when the user interacts with the main menu. It now handles disconnecting from the wallet and go to
the TON sending amount window.

#### Send Amount TON Handler

```python title="handlers.py"
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
```

This handler is triggered when a user interacts with the send amount TON window. It handles navigating back to the main
menu.

#### Send Amount TON Message Handler

```python title="handlers.py"
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
            await atc_manager.send_transaction(
                callbacks=callbacks,
                transaction=transaction,
            )

    # Delete the original message containing the amount input
    await message.delete()
```

This handler is triggered when a user sends a message in the send amount TON state. It validates the entered amount,
creates a TONTransferTransaction, and opens the window for sending the transaction.

#### Transaction Info Handler

```python title="handlers.py"
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
```

This handler is triggered when a user interacts with the transaction information window. It handles the transition back
to
the main menu.

### Running the Bot

To run the Bot, use the following command in your terminal:

```bash
python -m bot
```

The bot source code is available
on [GitHub](https://github.com/nessshon/aiogram-tonconnect/blob/main/example/sending-transaction/).