# 📦 aiogram TON Connect

[![TON](https://img.shields.io/badge/TON-grey?logo=TON&logoColor=40AEF0)](https://ton.org)
![Python Versions](https://img.shields.io/badge/Python-3.10%20--%203.14-black?color=FFE873&labelColor=3776AB)
[![PyPI](https://img.shields.io/pypi/v/aiogram-tonconnect.svg?color=FFE873&labelColor=3776AB)](https://pypi.python.org/pypi/aiogram-tonconnect)
[![License](https://img.shields.io/github/license/nessshon/aiogram-tonconnect)](https://github.com/nessshon/aiogram-tonconnect/blob/main/LICENSE)
[![Donate](https://img.shields.io/badge/Donate-TON-blue)](https://tonviewer.com/UQCZq3_Vd21-4y4m7Wc-ej9NFOhh_qvdfAkAYAOHoQ__Ness)

![Image](https://raw.githubusercontent.com/nessshon/aiogram-tonconnect/main/public/banner.png)

![Downloads](https://pepy.tech/badge/aiogram-tonconnect)
![Downloads](https://pepy.tech/badge/aiogram-tonconnect/month)
![Downloads](https://pepy.tech/badge/aiogram-tonconnect/week)

### [TON Connect](https://github.com/ton-connect) for [aiogram](https://github.com/aiogram/aiogram) bots

Wallet connection, transactions, and data signing in Telegram bots.  
The library shows the screens of each request and passes the results to your handlers as aiogram events.  
See the [example bot](https://github.com/nessshon/aiogram-tonconnect/blob/main/example/bot.py) or try the
[demo bot](https://t.me/aiogramTONConnectBot) in Telegram.

> Built on [ton-connect](https://github.com/nessshon/ton-connect), the Python SDK for TON Connect.

**Features**

- **Wallet Connection** — QR code, wallet list with pages, and a button that opens the chosen wallet
- **Requests** — send transactions, sign messages for gasless relays, sign text, binary, and cell data
- **TON Proof** — wallet ownership and data signature verification
- **Events** — results come to router handlers with status, error, and the wallet answer
- **Restarts** — sessions and pending requests live in the FSM storage and resume after a restart
- **Screens** — texts in any language, button styles, or your own screens

> Support this project — TON: `donate.ness.ton`  
> `UQCZq3_Vd21-4y4m7Wc-ej9NFOhh_qvdfAkAYAOHoQ__Ness`

## Installation

```bash
pip install aiogram-tonconnect
```

## Usage

```python
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
from ton_connect.models import Wallet

from aiogram_tonconnect import TonConnectContext, TonConnectEvent, TonConnectRouter, setup_tonconnect

BOT_TOKEN = "12345:qwerty"
MANIFEST_URL = "https://raw.githubusercontent.com/nessshon/aiogram-tonconnect/main/public/tonconnect-manifest.json"

dp = Dispatcher()
router = TonConnectRouter()


@dp.message(CommandStart())
async def start(message: Message, tc: TonConnectContext) -> None:
    # Shows the connect screen: QR code, wallet list, Back
    await tc.connect()


@router.connect()
async def connected(event: TonConnectEvent, wallet: Wallet | None) -> None:
    text = f"Connected: {wallet.account.address.to_str()}" if wallet else "Not connected"
    await event.message.edit_text(text)


async def main() -> None:
    bot = Bot(BOT_TOKEN)
    dp.include_router(router)
    setup_tonconnect(dp, bot, manifest_url=MANIFEST_URL)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
```

## Notes

- **Manifest** — the example uses a public one; host your own `tonconnect-manifest.json` for a real bot
- **Storage** — sessions and pending requests live in the FSM storage; use `RedisStorage` to keep them after a restart
- **TON Proof** — pass `TonProof` to `setup_tonconnect` to verify wallet ownership and signed data
- **Screens** — subclass `View` to change texts, language, the QR code, or whole screens
- **Cancel** — call `tc.cancel()` to end an operation before replacing its screen

## License

This repository is distributed under
the [MIT License](https://github.com/nessshon/aiogram-tonconnect/blob/main/LICENSE).
