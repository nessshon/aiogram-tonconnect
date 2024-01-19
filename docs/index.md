# Aiogram Ton Connect UI

<img src="https://telegra.ph//file/9e28473c8da8989fdf027.jpg">

## Introduction

**aiogram-tonconnect** is a library that simplifies the integration of TonConnect functionality into Telegram bots
developed with the aiogram framework.

#### Features

* Ready-to-Use User Interface
* Middleware Functionality
* Interface Customization
* Multilingual Support
* QR Code Generation

### Concept

The library concept is based on predefined logic for processing and switching between bot windows. To implement it, you
need to install the middleware and register a handler. You then have access to `atc_manager`, which can be accessed in
handlers; it provides custom transitions between windows to connect to a wallet or send a transaction.

There are two main methods within the library: `connect_wallet` and `send_transaction`.

* The `connect_wallet` method is used to direct the user to the wallet connection menu, where a QR code and wallet
  selection buttons are generated.

* The `send_transaction` method is used to initiate the sending of a transaction. It triggers a transaction confirmation
  request to the user's wallet.

---