import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram_tonconnect.handlers import AiogramTonConnectHandlers
from aiogram_tonconnect.middleware import AiogramTonConnectMiddleware

from .handlers import router
from .throttling import ThrottlingMiddleware

# Your bot token
BOT_TOKEN = "1234567890:QWERTYUIOPASDFGHJKLZXCVBNM"

# Redis address
REDIS_DSN = "redis://localhost:6379/0"

# Link to your created manifest.json
MANIFEST_URL = "https://raw.githubusercontent.com/nessshon/aiogram-tonconnect/main/tonconnect-manifest.json"

# List of wallets to exclude
# Example:
# EXCLUDE_WALLETS = ["mytonwallet"]
EXCLUDE_WALLETS = []


async def main():
    # Initializing the storage for FSM (Finite State Machine)
    storage = RedisStorage.from_url(os.environ.get("REDIS_DSN", REDIS_DSN))

    # Creating a bot object with the token and HTML parsing mode
    bot = Bot(os.environ.get("BOT_TOKEN", BOT_TOKEN), parse_mode="HTML")

    # Creating a dispatcher object using the specified storage
    dp = Dispatcher(storage=storage)

    dp.update.middleware.register(ThrottlingMiddleware())
    # Registering middleware for TON Connect processing
    dp.update.middleware.register(
        AiogramTonConnectMiddleware(
            redis=storage.redis,
            manifest_url=MANIFEST_URL,
            exclude_wallets=EXCLUDE_WALLETS,
        )
    )

    # Registering TON Connect handlers
    AiogramTonConnectHandlers().register(dp)

    # Including the router
    dp.include_router(router)

    # Starting the bot using long polling
    await dp.start_polling(bot)


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
