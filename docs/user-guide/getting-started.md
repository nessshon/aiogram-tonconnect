### Installation

Install the library:

```bash
pip install aiogram-tonconnect
```

Additionally, you will need to install Redis to store data about connected wallets.

```bash
apt install redis
```

### Creating manifest.json

Before you need to create a manifest to pass meta-information to the wallet.
The manifest is a JSON file with the following format:

```json title="tonconnect-manifest.json"
{
    "url": "<app-url>",                        // required
    "name": "<app-name>",                      // required
    "iconUrl": "<app-icon-url>",               // required
    "termsOfUseUrl": "<terms-of-use-url>",     // optional
    "privacyPolicyUrl": "<privacy-policy-url>" // optional
}
```

Where:

* `url`: Link to your bot or your website.
* `name`: The name of your bot or your website.
* `iconUrl`: Link to the avatar of your bot or your website.
* `termsOfUseUrl`: Link to the terms of use (optional).
* `privacyPolicyUrl`: Link to the privacy policy (optional).

**Note:** Host this file on a hosting service or GitHub so that it is accessible via a link.

---

### Bot structure

The primary structure of the bot includes the following elements:

```plaintext
bot/
├── __init__.py
├── __main__.py
├── handlers.py
├── windows.py
```

Where:

* `__init__.py`: Informs Python that the bot folder should be treated as a package.
* `__main__.py`: The main file where the bot object created, and the dispatcher is configured.
* `handlers.py`: A module containing event and command handlers.
* `windows.py`: A module where functions for creating bot windows are defined.

---

### Bot initialization

Open the `__main__.py` file and insert the following code:

```python title="__main__.py"
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram_tonconnect.handlers import AiogramTonConnectHandlers
from aiogram_tonconnect.middleware import AiogramTonConnectMiddleware

# Your bot token
BOT_TOKEN = "1234567890:QWERTYUIOPASDFGHJKLZXCVBNM"

# Redis address
REDIS_DSN = "redis://localhost:6379/0"

# Link to your created manifest.json
MANIFEST_URL = "https://raw.githubusercontent.com/nessshon/aiogram-tonconnect/main/tonconnect-manifest.json"

# List of wallets to exclude
EXCLUDE_WALLETS = ["mytonwallet"]


async def main():
    # Initializing the storage for FSM (Finite State Machine)
    storage = RedisStorage.from_url(REDIS_DSN)

    # Creating a bot object with the token and HTML parsing mode
    bot = Bot(BOT_TOKEN, parse_mode="HTML")

    # Creating a dispatcher object using the specified storage
    dp = Dispatcher(storage=storage)

    # Registering middleware for TON Connect processing
    dp.update.middleware.register(
        AiogramTonConnectMiddleware(
            redis=storage.redis,
            manifest_url=MANIFEST_URL,
            exclude_wallets=EXCLUDE_WALLETS,
            qrcode_type="url",  # or "bytes" if you prefer to generate QR codes locally.
        )
    )

    # Registering TON Connect handlers
    AiogramTonConnectHandlers().register(dp)

    # Starting the bot using long polling
    await dp.start_polling(bot)


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
```

**Note**: Ensure that you replace the values of the variables `BOT_TOKEN`, `REDIS_DSN`, and others with the actual ones.
