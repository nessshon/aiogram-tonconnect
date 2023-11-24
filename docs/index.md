# Aiogram Ton Connect Library

## Introduction

The aiogram-tonconnect library provides a ready-to-use UI for TON Connect in Telegram bots based on the aiogram
framework. It serves as a wrapper around the core code, seamlessly integrated through middleware and handler
registration.

Developers, especially those new to the field, often face challenges in creating a functional UI for TON Connect—from
displaying wallet selection buttons and generating QR codes to handling and presenting user warnings about transaction
cancellations and timeout errors. This library aims to address these complexities, simplifying the integration of TON
Connect into Telegram bots.

## Concept

The library's concept revolves around pre-built logic for handling, processing, and switching between bot windows and
states. Developers need only to install the middleware and register handlers. Subsequently, they gain access to the
aiogram-tonconnect manager, enabling user transitions to wallet connection or transaction submission windows.
Communication between the developer's code and the library occurs through callback handlers.

To open the wallet connection window, developers need to specify two callback functions: `before_callback` and
`after_callback`. The former manages user window transitions during navigation and back button presses, while the latter
triggers after a successful connection or confirmed transaction. All relevant information is passed as arguments to the
function, allowing developers to utilize it as needed.

## Features

### QRCode Generation Service

The library includes a built-in QR code generation service that operates behind the scenes. It generates QR codes
using
query parameters, which accept a base64-encoded universal URL from TON Connect. The library decodes this URL on the
backend and presents it as a web page preview for enhanced visual appeal and smooth window transitions. The QR code
generation service is open-source, allowing users to override the default provider class for QR code generation,
potentially improving response speed.

### Interface Customization

The library provides complete customization of all interface elements, including button text and messages. Users can
inherit from the base class and override values according to their preferences.

### Multilingual Support

The library offers built-in support for multilingual interfaces. Users can inherit from the base classes and add text
translations in their preferred language.