# aiogram TON Connect

[![PyPI](https://img.shields.io/pypi/v/aiogram-tonconnect.svg)](https://pypi.python.org/pypi/aiogram-tonconnect)
![Python Versions](https://img.shields.io/pypi/pyversions/aiogram-tonconnect.svg)
![License](https://img.shields.io/github/license/nessshon/aiogram-tonconnect)

**aiogram-tonconnect** is a library that simplifies the integration of TonConnect functionality into Telegram bots
developed with the aiogram framework.
It provides a ready-to-use UI and handles the interaction flow for connecting wallets and
sending transactions. This library acts as a middleware, making it easy to incorporate TonConnect features into your
existing aiogram-based bots.

Check out the [documentation](https://nessshon.github.io/aiogram-tonconnect/).\
Bot example [@aiogramTONConnectBot](https://t.me/aiogramTONConneсtBot/).

## Installation

```bach
pip install aiogram-tonconnect
```

## Features
* **TonConnect Integration:**

    Simplifies the integration of TonConnect functionality with Telegram bots.

* **Built with Aiogram:**

    Developed using the Aiogram framework, providing convenience in operation.

* **Ready-to-Use User Interface:**

    Offers a ready-to-use user interface that manages the interaction flow for connecting to wallets and sending transactions.

* **Middleware Functionality:**

    Acts as middleware, making it easier to incorporate TonConnect features into existing Aiogram-based bots.

* **Multilingual Support:**

    Supports multiple languages, making it easy to add new languages and translate messages and button texts.

* **QR Code Provider:**

    Includes a QR code provider that generates QR codes for connecting to wallets. There is an option to deploy a custom QR code provider API with open-source code on [GitHub](https://github.com/nessshon/qrcode-fastapi), speeding up response time and reducing load on the public API.

* **Full Customization:**

    Allows complete customization of texts and buttons. Simply inherit the base class and insert your own texts.

## Screenshots

<a href="https://telegra.ph//file/3608fb4c335d5a4cd6fd2.jpg" target="_blank">
  <img src="https://telegra.ph//file/3608fb4c335d5a4cd6fd2.jpg" width="100" alt="Image 1">
</a>
<a href="https://telegra.ph//file/a90b6affec7e267f60320.jpg" target="_blank">
  <img src="https://telegra.ph//file/a90b6affec7e267f60320.jpg" width="100" alt="Image 3">
</a>
<a href="https://telegra.ph//file/8730c64a11601c6ed6884.jpg" target="_blank">
  <img src="https://telegra.ph//file/8730c64a11601c6ed6884.jpg" width="100" alt="Image 2">
</a>
<a href="https://telegra.ph//file/5a49ffa9f8330f66cdcac.jpg" target="_blank">
  <img src="https://telegra.ph//file/5a49ffa9f8330f66cdcac.jpg" width="100" alt="Image 4">
</a>

## Contributions

Contributions, bug reports, and feature requests are welcome. Please feel free to create issues and pull requests.

## License

aiogram-tonconnect is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

This project utilizes the following dependencies to enhance its functionality:

- [**aiofiles:**](https://pypi.org/project/aiofiles/) Asynchronous file operations.
- [**aiogram:**](https://pypi.org/project/aiogram/) An asynchronous framework for building Telegram bots.
- [**aiohttp:**](https://pypi.org/project/aiohttp/) An asynchronous HTTP client/server framework.
- [**cachetools:**](https://pypi.org/project/cachetools/) A set of caching utilities.
- [**pydantic:**](https://pypi.org/project/pydantic/) Data validation and settings management using Python type hints.
- [**pytonconnect:**](https://pypi.org/project/pytonconnect/) Python SDK for TON Connect 2.0.
- [**pytoniq-core:**](https://pypi.org/project/pytoniq-core/) TON Blockchain primitives.
- [**redis:**](https://pypi.org/project/redis/) A Python client for Redis, an in-memory data structure store.
- [**qrcode-fastapi:**](https://github.com/nessshon/qrcode-fastapi) Generate QR codes with optional image inclusion,
  supports base64-encoded.

We extend our gratitude to the maintainers and contributors of these libraries for their valuable contributions to the
open-source community.

## Donations

<a href="https://app.tonkeeper.com/transfer/EQC-3ilVr-W0Uc3pLrGJElwSaFxvhXXfkiQA3EwdVBHNNess"><img src="https://telegra.ph//file/8e0ac22311be3fa6f772c.png" width="55"/></a>
<a href="https://tonhub.com/transfer/EQC-3ilVr-W0Uc3pLrGJElwSaFxvhXXfkiQA3EwdVBHNNess"><img src="https://telegra.ph//file/7fa75a1b454a00816d83b.png" width="55"/></a>\
```EQC-3ilVr-W0Uc3pLrGJElwSaFxvhXXfkiQA3EwdVBHNNess```
