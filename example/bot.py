from __future__ import annotations

from dataclasses import dataclass

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage
from aiogram_tonconnect.handlers import AiogramTonConnectHandlers
from aiogram_tonconnect.middleware import AiogramTonConnectMiddleware
from aiogram_tonconnect.tonconnect.storage import ATCRedisStorage
from aiogram_tonconnect.utils.qrcode import QRUrlProvider
from tonutils.tonconnect import TonConnect
from environs import Env

from handlers import router
from throttling import ThrottlingMiddleware


@dataclass
class Config:
    """
    Configuration for the bot.

    Contains bot token, Redis connection string, and TonConnect manifest URL.
    """

    BOT_TOKEN: str
    REDIS_DSN: str
    MANIFEST_URL: str

    @classmethod
    def load(cls) -> Config:
        """
        Load configuration from environment variables.
        """
        env = Env()
        env.read_env()

        return cls(
            BOT_TOKEN=env.str("BOT_TOKEN"),
            REDIS_DSN=env.str("REDIS_DSN"),
            MANIFEST_URL=env.str("MANIFEST_URL"),
        )


async def main():
    """
    Main entry point for the bot.
    Initializes the bot, middlewares, and starts polling.
    """
    config = Config.load()

    # Initialize Redis storage for FSM
    storage = RedisStorage.from_url(config.REDIS_DSN)
    bot = Bot(config.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher(storage=storage)

    # Register throttling middleware to control request rates
    dp.update.middleware.register(ThrottlingMiddleware())

    # Set up TonConnect integration
    tonconnect = TonConnect(
        manifest_url=config.MANIFEST_URL,
        storage=ATCRedisStorage(storage.redis),
        wallets_fallback_file_path="./wallets.json",
    )
    dp.update.middleware.register(
        AiogramTonConnectMiddleware(
            tonconnect=tonconnect,
            qrcode_provider=QRUrlProvider(),
        )
    )

    # Register TonConnect-specific handlers
    AiogramTonConnectHandlers().register(dp)

    # Include application-specific routers
    dp.include_router(router)

    # Start polling for updates
    await dp.start_polling(bot)


if __name__ == '__main__':
    import asyncio

    # Run the main function
    asyncio.run(main())
