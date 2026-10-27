from __future__ import annotations

import typing as t

from aiogram import Bot, Dispatcher
from ton_connect import TonConnect

from .core.storage import Storage
from .manager import TonConnectManager
from .view import View

if t.TYPE_CHECKING:
    from ton_connect.models import AppWallet
    from ton_core import NetworkGlobalID

    from .core.proof import TonProof


def setup_tonconnect(
    dispatcher: Dispatcher,
    *bots: Bot,
    manifest_url: str,
    view: View | None = None,
    wallets: list[AppWallet] | None = None,
    network: NetworkGlobalID | None = None,
    redirect_url: str | None = None,
    ton_proof: TonProof | None = None,
    headers: dict[str, str] | None = None,
) -> TonConnectManager:
    """Add TON Connect to a dispatcher.

    Handlers in private chats get ``tc``, ``TonConnectRouter`` handlers get the results. Sessions and pending
    operations live in the FSM storage and are resumed on startup.

    :param bots: The bots of the dispatcher; the operations of their users resume on startup.
    :param manifest_url: URL of ``tonconnect-manifest.json``.
    :param view: Screens of the operations; ``View()`` by default.
    :param wallets: Wallet catalog, the public one by default; wallets without a universal link are skipped.
    :param network: Network the wallet must be on, or ``None`` for any.
    :param redirect_url: Where the wallet returns the user after the Open button; the chat with the bot by default.
    :param ton_proof: Checks of ``ton_proof`` on connect and of ``sign_data`` signatures; none by default.
    :param headers: Extra HTTP headers for the bridges.
    """
    if not bots:
        raise ValueError("At least one bot is required")
    storage = Storage(dispatcher.storage)
    tonconnect = TonConnect(storage, manifest_url, [], headers=headers)
    return TonConnectManager(
        dispatcher, list(bots), tonconnect, storage, view or View(), wallets, network, redirect_url, ton_proof
    )
