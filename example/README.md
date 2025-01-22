# Bot Setup and Usage

This repository contains a Python bot built using the `aiogram` framework with integrated TonConnect support.

## Requirements

- Python 3.10+
- Redis server

## Installation

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Create a JSON file describing your application:
   ```
   {
     "url": "<app-url>",                        // required
     "name": "<app-name>",                      // required
     "iconUrl": "<app-icon-url>",               // required
     "termsOfUseUrl": "<terms-of-use-url>",     // optional
     "privacyPolicyUrl": "<privacy-policy-url>" // optional
   }
   ```
   **Note**: Ensure this file is publicly accessible via its URL.

3. Create a `.env` file from the example:

   ```bash
   cp env.example .env
   ```

4. Update `.env` with your configuration:

    * **BOT_TOKEN**: Your Telegram Bot Token.
    * **MANIFEST_URL**: TonConnect manifest URL.
    * **REDIS_DSN**: Redis connection string (e.g., redis://localhost:6379/0).

5. Run the bot:

   ```bash
   python bot.py
   ```
