import asyncio
import html
import logging
import os
import secrets
from collections.abc import Awaitable, Callable
from typing import Any

import aiohttp
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, TelegramObject
from dotenv import load_dotenv
from ton_connect.models import (
    SendTransactionMessage,
    SendTransactionPayload,
    SendTransactionResult,
    SignDataPayloadText,
    SignDataResult,
    SignMessageResult,
    Wallet,
)
from ton_core import Address, JettonTransferBody, TextCommentBody, cell_to_b64, norm_stack_cell, to_nano

from aiogram_tonconnect import (
    DisconnectEvent,
    TonConnectContext,
    TonConnectEvent,
    TonConnectRouter,
    TonProof,
    setup_tonconnect,
)

# Settings come from example/.env, a copy of .env.example
load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]
TON_PROOF_SECRET = os.environ["TON_PROOF_SECRET"]

# The manifest of this example; a bot in production hosts its own. Its "url" is on the host that serves the file,
# or a wallet may reject it; wallets sign ton_proof for that host
MANIFEST_URL = "https://raw.githubusercontent.com/nessshon/aiogram-tonconnect/main/public/tonconnect-manifest.json"
MANIFEST_DOMAIN = "raw.githubusercontent.com"

# Tether USD₮ jetton master on mainnet
USDT_MASTER, USDT_DECIMALS = "EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs", 6

# Commands and buttons that work without a wallet
menu_router = Router()
# Buttons that need a wallet: wallet_required_middleware opens the connect screen when there is none
wallet_router = Router()
# Results of tc operations, sent by the wallet
tc_router = TonConnectRouter()


class Order(CallbackData, prefix="order"):
    id: str
    amount: str
    currency: str


def shorten(value: str) -> str:
    return f"{value[:4]}…{value[-4:]}"


def address_link(address: Address) -> str:
    address_str = address.to_str(is_bounceable=False)
    return f'<a href="https://gram.org/address/{address_str}">{shorten(address_str)}</a>'


def transaction_link(message_hash: str) -> str:
    return f'<a href="https://gram.org/tx/by-msg-hash/{message_hash}">{shorten(message_hash)}</a>'


def connect_markup() -> InlineKeyboardMarkup:
    inline_keyboard = [[InlineKeyboardButton(text="Connect Wallet", callback_data="connect", style="primary")]]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def actions_markup() -> InlineKeyboardMarkup:
    gram_order = Order(id=secrets.token_hex(4), amount="0.1", currency="GRAM")
    usdt_order = Order(id=secrets.token_hex(4), amount="0.1", currency="USD₮")
    inline_keyboard = [
        [InlineKeyboardButton(text=f"Pay {gram_order.amount} {gram_order.currency}", callback_data=gram_order.pack())],
        [InlineKeyboardButton(text=f"Pay {usdt_order.amount} {usdt_order.currency}", callback_data=usdt_order.pack())],
        [InlineKeyboardButton(text="Sign Message", callback_data="sign_message")],
        [InlineKeyboardButton(text="Sign Data", callback_data="sign_data")],
        [InlineKeyboardButton(text="Disconnect", callback_data="disconnect", style="danger")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def build_wallet_menu(tc: TonConnectContext, result_text: str = "") -> tuple[str, InlineKeyboardMarkup]:
    if tc.wallet is None:
        return "<b>Wallet not connected</b>\n\nConnect a wallet to pay and sign.", connect_markup()
    wallet_name = tc.app_wallet.name if tc.app_wallet is not None else "Wallet"
    address = address_link(tc.wallet.account.address)
    blocks = [f"<b>{html.escape(wallet_name)}</b> · {address}", result_text, "Choose an action:"]
    return "\n\n".join(block for block in blocks if block), actions_markup()


async def get_usdt_wallet_address(owner_address: Address) -> Address:
    request = {
        "address": USDT_MASTER,
        "method": "get_wallet_address",
        "stack": [{"type": "slice", "value": cell_to_b64(owner_address.to_cell())}],
    }
    async with (
        aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session,
        session.post("https://toncenter.com/api/v3/runGetMethod", json=request) as response,
    ):
        response.raise_for_status()
        result = await response.json()
    address = norm_stack_cell(result["stack"][0]["value"])
    assert isinstance(address, Address)
    # A jetton wallet is a contract: a failed transfer must bounce back
    address.is_bounceable = True
    return address


@menu_router.message(CommandStart())
async def start(message: Message, tc: TonConnectContext) -> None:
    # A new menu replaces any screen of a running operation: end it, or it would finish there later
    await tc.cancel()
    text, markup = build_wallet_menu(tc)
    await message.answer(text, reply_markup=markup)


@menu_router.callback_query(F.data == "connect")
async def connect(query: CallbackQuery, tc: TonConnectContext) -> None:
    await query.answer()
    await tc.connect()


@menu_router.callback_query(F.data == "disconnect")
async def disconnect(query: CallbackQuery, tc: TonConnectContext) -> None:
    await query.answer()
    await tc.disconnect()


@wallet_router.callback_query(Order.filter(F.currency == "GRAM"))
async def pay_gram(query: CallbackQuery, callback_data: Order, wallet: Wallet, tc: TonConnectContext) -> None:
    await query.answer()
    # The wallet pays itself, so only the fee is spent; the comment lets you find the payment on chain
    transfer = SendTransactionMessage(
        address=wallet.account.address,
        amount=to_nano(callback_data.amount),
        payload=f"Order {callback_data.id}",
    )
    await tc.send_transaction(SendTransactionPayload(messages=[transfer]), payload=callback_data)


@wallet_router.callback_query(Order.filter(F.currency == "USD₮"))
async def pay_usdt(query: CallbackQuery, callback_data: Order, wallet: Wallet, tc: TonConnectContext) -> None:
    await query.answer()
    wallet_address = wallet.account.address
    usdt_wallet_address = await get_usdt_wallet_address(wallet_address)
    jetton_transfer = JettonTransferBody(
        destination=wallet_address,
        jetton_amount=to_nano(callback_data.amount, USDT_DECIMALS),
        response_address=wallet_address,
        forward_payload=TextCommentBody(f"Order {callback_data.id}").serialize(),
    )
    # The attached TON pays the jetton transfer fee; the change returns to response_address
    transfer = SendTransactionMessage(
        address=usdt_wallet_address,
        amount=to_nano("0.05"),
        payload=jetton_transfer.serialize(),
    )
    await tc.send_transaction(SendTransactionPayload(messages=[transfer]), payload=callback_data)


@wallet_router.callback_query(F.data == "sign_message")
async def sign_message(query: CallbackQuery, wallet: Wallet, tc: TonConnectContext) -> None:
    await query.answer()
    transfer = SendTransactionMessage(address=wallet.account.address, amount=to_nano("0.1"))
    await tc.sign_message(SendTransactionPayload(messages=[transfer]))


@wallet_router.callback_query(F.data == "sign_data")
async def sign_data(query: CallbackQuery, bot: Bot, tc: TonConnectContext) -> None:
    await query.answer()
    data = SignDataPayloadText(text=f"I agree to the terms of @{(await bot.me()).username}")
    await tc.sign_data(data)


@tc_router.connect()
async def on_connect(event: TonConnectEvent, tc: TonConnectContext) -> None:
    text, markup = build_wallet_menu(tc)
    await event.message.edit_text(text, reply_markup=markup)


@tc_router.transaction()
async def on_transaction(event: TonConnectEvent, tc: TonConnectContext, result: SendTransactionResult | None) -> None:
    result_text = ""
    if result is not None and event.payload is not None:
        order = Order.unpack(event.payload)
        # The wallet has sent it, but it may not be on chain yet: check by the hash or the comment
        result_text = (
            "<b>Order sent</b>\n"
            f"ID: <code>{order.id}</code>\n"
            f"Amount: {order.amount} {order.currency}\n"
            f"Transaction: {transaction_link(result.normalized_hash)}"
        )
    text, markup = build_wallet_menu(tc, result_text)
    await event.message.edit_text(text, reply_markup=markup)


@tc_router.sign_message()
async def on_sign_message(event: TonConnectEvent, tc: TonConnectContext, result: SignMessageResult | None) -> None:
    result_text = ""
    if result is not None:
        result_text = (
            "<b>Message signed</b>\n"
            "Not sent: a relayer sends it and may pay the fee.\n"
            f"<code>{shorten(result.internal_boc)}</code>"
        )
    text, markup = build_wallet_menu(tc, result_text)
    await event.message.edit_text(text, reply_markup=markup)


@tc_router.sign_data()
async def on_sign_data(event: TonConnectEvent, tc: TonConnectContext, result: SignDataResult | None) -> None:
    result_text = ""
    if result is not None and isinstance(result.payload, SignDataPayloadText):
        # The text comes back from the wallet; ton_proof has already checked its signature
        result_text = f"<b>Data signed</b>\n<blockquote>{html.escape(result.payload.text)}</blockquote>"
    text, markup = build_wallet_menu(tc, result_text)
    await event.message.edit_text(text, reply_markup=markup)


@tc_router.disconnect()
async def on_disconnect(event: DisconnectEvent, tc: TonConnectContext) -> None:
    text, markup = build_wallet_menu(tc)
    await event.message.edit_text(text, reply_markup=markup)


async def wallet_required_middleware(
    handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
    event: TelegramObject,
    data: dict[str, Any],
) -> Any:
    tc: TonConnectContext = data["tc"]
    if tc.wallet is not None:
        data["wallet"] = tc.wallet
        return await handler(event, data)
    await tc.connect()
    if isinstance(event, CallbackQuery):
        await event.answer()
    return None


async def main() -> None:
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    # MemoryStorage loses sessions and waiting operations on restart; RedisStorage keeps them
    dp = Dispatcher()
    # The wallet proves it owns the address on connect, and sign_data signatures are checked
    ton_proof = TonProof(domain=MANIFEST_DOMAIN, secret=TON_PROOF_SECRET)
    setup_tonconnect(dp, bot, manifest_url=MANIFEST_URL, ton_proof=ton_proof)
    wallet_router.callback_query.middleware(wallet_required_middleware)
    dp.include_routers(menu_router, wallet_router, tc_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
