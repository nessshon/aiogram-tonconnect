## aiogram TON Connect Bot

This Telegram bot, built using the aiogram-tonconnect library, serves as an example to demonstrate the integration of
Ton Connect in Telegram bots based on the Aiogram framework. The bot provides a user interface for seamless interaction
with Ton Connect features.

Bot example: [@aiogramTONConnectBot](https://t.me/aiogramTONConncetBot)

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/nessshon/aiogram-tonconnect.git
    ```

2. Change into the bot directory:

    ```bash
    cd aiogram-tonconnect/example
    ```
3. Clone environment variables file:

   ```bash
   cp .env.example .env
   ```

4. Configure [environment variables](#environment-variables-reference) variables file:

   ```bash
   nano .env
   ```

5. Running a bot in a docker container:

   ```bash
   docker-compose up --build
   ```

## Environment Variables Reference

Here is a reference guide for the environment variables used in the project:

| Variable  | Description                                                   | Example                               |
|-----------|---------------------------------------------------------------|---------------------------------------|
| BOT_TOKEN | Bot token, obtained from [@BotFather](https://t.me/BotFather) | 1234567890:QWERTYUIOPASDFGHJKLZXCVBNM | 
| REDIS_DSN | Redis DSN - Connection string for the Redis server            | redis://redis:6379/0                  |
