# 📦 aiogram TON Connect

[![TON](https://img.shields.io/badge/TON-grey?logo=TON&logoColor=40AEF0)](https://ton.org)
[![PyPI](https://img.shields.io/pypi/v/aiogram-tonconnect.svg?color=FFE873&labelColor=3776AB)](https://pypi.python.org/pypi/aiogram-tonconnect)
![Python Versions](https://img.shields.io/badge/Python-3.7%20--%203.12-black?color=FFE873&labelColor=3776AB)
[![License](https://img.shields.io/github/license/tonmendon/aiogram-tonconnect)](https://github.com/tonmendon/aiogram-tonconnect/blob/main/LICENSE)


<img src="https://telegra.ph//file/9e28473c8da8989fdf027.jpg">

![Downloads](https://pepy.tech/badge/aiogram-tonconnect)
![Downloads](https://pepy.tech/badge/aiogram-tonconnect/month)
![Downloads](https://pepy.tech/badge/aiogram-tonconnect/week)

**aiogram-tonconnect** is a library that simplifies the integration of TonConnect functionality into Telegram bots
developed with the aiogram framework.
It provides a ready-to-use UI and handles the interaction flow for connecting wallets and
sending transactions. This library acts as a middleware, making it easy to incorporate TonConnect features into your
existing aiogram-based bots.

Check out the [documentation](https://tonmendon.github.io/aiogram-tonconnect/).\
Bot example [@aiogramTONConnectBot](https://t.me/aiogramTONConnectBot/).

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

  Offers a ready-to-use user interface that manages the interaction flow for connecting to wallets and sending
  transactions.

* **Middleware Functionality:**

  Acts as middleware, making it easier to incorporate TonConnect features into existing Aiogram-based bots.

* **Multilingual Support:**

  Supports multiple languages, making it easy to add new languages and translate messages and button texts.

* **QR Code Provider:**

  Includes a QR code provider that generates QR codes for connecting to wallets. There is an option to deploy a custom
  QR code provider API with open-source code on [GitHub](https://github.com/nessshon/qrcode-fastapi), speeding up
  response time and reducing load on the public API.

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

## Acknowledgments

This project utilizes the following dependencies to enhance its functionality:

- [**aiogram:**](https://pypi.org/project/aiogram/) An asynchronous framework for building Telegram bots.
- [**pytonconnect:**](https://pypi.org/project/pytonconnect/) Python SDK for TON Connect 2.0.
- [**pytoniq-core:**](https://pypi.org/project/pytoniq-core/) TON Blockchain primitives.
- [**qrcode-fastapi:**](https://github.com/nessshon/qrcode-fastapi) Generate QR codes with optional image inclusion,
  supports base64-encoded.
- and more...

We extend our gratitude to the maintainers and contributors of these libraries for their valuable contributions to the
open-source community.

## Contribution

We welcome your contributions! If you have ideas for improvement or have identified a bug, please create an issue or
submit a pull request.

## Donations

**TON** - `EQC-3ilVr-W0Uc3pLrGJElwSaFxvhXXfkiQA3EwdVBHNNess`

**USDT** (TRC-20) - `TJjADKFT2i7jqNJAxkgeRm5o9uarcoLUeR`

## License

This repository is distributed under
the [MIT License](https://github.com/tonmendon/aiogram-tonconnect/blob/main/LICENSE). Feel free to use, modify, and
distribute the code in accordance with the terms of the license.