## Window Descriptions

For our simple example, we will need only two bot windows:

* `select_language` - Language Selection:
  This window can be used to provide the user with the choice of language when first interacting with the bot, for
  example, after the /start command and when pressing the back button in the wallet connection window.

* `main_menu` - Main Menu:
  After successfully connecting the wallet, the user can access the main menu, where they can navigate to the
  transaction sending window and disconnect from the wallet.

Other windows, such as wallet selection, wallet connection, handling timeout errors, and canceling transactions, will be
automatically handled by aiogram-tonconnect, significantly simplifying routine tasks.

---

## Let's writing windows.

Open the file `windows.py`

### Creating States

Firstly, let's define the user state class to manage transitions and save necessary data:

```python
from aiogram.fsm.state import StatesGroup, State


class UserState(StatesGroup):
    select_language = State()
    main_menu = State()
```

### Creating Window Functions

#### Window `select_language`

```python
...
from aiogram.types import InlineKeyboardButton as Button
from aiogram.types import InlineKeyboardMarkup as Markup
from aiogram_tonconnect import ATCManager


async def select_language_window(atc_manager: ATCManager, **_) -> None:
    # Depending on the user's language, a message will be displayed.
    text = (
        "Select the language:"
        if atc_manager.user.language_code == "en" else
        "Выберите язык:"
    )
    # Creating a keyboard with buttons
    inline_keyboard = [
        [Button(text="English", callback_data="en"),
         Button(text="Русский", callback_data="ru")],
    ]
    reply_markup = Markup(inline_keyboard=inline_keyboard)

    # Sending the message
    await atc_manager.send_message(text, reply_markup=reply_markup)
    # Setting the state to select_language
    await atc_manager.state.set_state(UserState.select_language)
```

Where:

* `atc_manager`: **ATCManager**
  This is the main control class of aiogram-tonconnect. It is passed to handlers through middleware and is available for
  calling.
* `**_`: **Kwargs**
  These are other parameters. The library passes all data from middleware data (bot, state, event_from_user, etc.) in an
  unpacked form, and they are available for calling.
  For example, you can specify `async def select_language_window(atc_manager: ATCManager, bot: Bot, **_) -> None:` and
  use the bot object for your needs.

#### Window `main_menu`

```python
...
from aiogram_tonconnect.tonconnect.models import AccountWallet


async def main_menu_window(atc_manager: ATCManager, **data) -> None:
    # After successfully connecting the wallet, the library passes account_wallet with data about the connected wallet
    # extract information from data under the key account_wallet
    account_wallet: AccountWallet = data.get("account_wallet", None)

    # Since our main_menu_window works in the middle, between connection and transaction sending,
    # we check additionally whether the function received account_wallet or not
    # if it didn't, it means the transaction was called a step earlier
    if not account_wallet:
        # therefore, we extract wallet information from the atc_manager
        account_wallet = atc_manager.user.account_wallet

    # Display a message with the connected wallet
    text = (
        f"Connected wallet: \n{account_wallet.address}\n\n"
        if atc_manager.user.language_code == "en" else
        f"Подключенный кошелек: \n{account_wallet.address}\n\n"
    )

    # Check if the previous step was a transaction, then extract the response from tonconnect
    # under the key transaction_boc
    transaction_boc = data.get("transaction_boc", None)
    if transaction_boc:
        # If transaction_boc is found, it means everything is correct, the previous user step was
        # sending a transaction, add transaction information to the message
        text += (
            f"Last transaction: \n{transaction_boc or '-'}\n\n"
            if atc_manager.user.language_code == "en" else
            f"Последняя транзакция: \n{transaction_boc or '-'}\n\n"
        )

    button_send_transaction_text = (
        "Send transaction"
        if atc_manager.user.language_code == "en" else
        "Отправить транзакцию"
    )
    button_disconnect_text = (
        "Disconnect"
        if atc_manager.user.language_code == "en" else
        "Отключиться"
    )
    inline_keyboard = [
        [Button(text=button_send_transaction_text, callback_data="send_transaction")],
        [Button(text=button_disconnect_text, callback_data="disconnect")],
    ]
    reply_markup = Markup(inline_keyboard=inline_keyboard)

    await atc_manager.send_message(text, reply_markup=reply_markup)
    await atc_manager.state.set_state(UserState.send_transaction)
```