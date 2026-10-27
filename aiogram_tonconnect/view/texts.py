import typing as t
from dataclasses import dataclass, field

from aiogram.enums import ButtonStyle


@dataclass(frozen=True)
class Texts:
    """Texts of the screens in one language, in HTML.

    ``connect`` and ``confirm_*`` take ``{wallet_name}`` and ``{minutes}``, what is left of the operation rounded up;
    ``open_wallet`` takes ``{wallet_name}``.
    """

    connect: str = (
        "<b>Connect your wallet</b>\n\nScan the QR code with {wallet_name} or choose your wallet below.\n\n"
        "<i>The link is valid for {minutes} min.</i>"
    )
    confirm_transaction: str = (
        "<b>Confirm the transaction</b>\n\nOpen {wallet_name} and confirm it there.\n\n"
        "<i>The request is valid for {minutes} min.</i>"
    )
    confirm_sign_message: str = (
        "<b>Sign the transaction</b>\n\nOpen {wallet_name} and sign it there.\n\n"
        "<i>The request is valid for {minutes} min.</i>"
    )
    confirm_sign_data: str = (
        "<b>Sign the data</b>\n\nOpen {wallet_name} and sign it there.\n\n"
        "<i>The request is valid for {minutes} min.</i>"
    )
    rejected: str = "<b>Declined</b>\n\nThe request was declined in the wallet."
    timeout: str = "<b>Time is up</b>\n\nThe wallet did not answer in time."
    wrong_network: str = "<b>Wrong network</b>\n\nThe wallet is on another TON network."
    bad_signature: str = "<b>Not verified</b>\n\nThe wallet signature did not pass the check."
    bad_manifest: str = "<b>Manifest error</b>\n\nThe wallet rejected the manifest of this bot."
    not_supported: str = "<b>Not supported</b>\n\nThis wallet cannot do what was asked."
    not_connected: str = "<b>No wallet</b>\n\nConnect a wallet first."
    unavailable: str = "<b>Wallet service unavailable</b>\n\nIt is overloaded or down. Try again later."
    failed: str = "<b>Something went wrong</b>\n\nTry again a bit later."
    open_wallet: str = "Open {wallet_name}"
    go_back: str = "‹ Back"
    unknown_wallet: str = "your wallet"
    """``{wallet_name}`` of a wallet missing from the catalog."""


@dataclass(frozen=True)
class ButtonStyles:
    """Styles of the buttons: ``primary``, ``success``, ``danger`` or ``None`` for the default; icons of the wallets."""

    open_wallet: ButtonStyle | None = ButtonStyle.PRIMARY
    selected_wallet: ButtonStyle | None = None
    go_back: ButtonStyle | None = None
    wallet_icons: t.Mapping[str, str] = field(default_factory=dict)
    """Custom emoji ID by wallet ``app_name``."""
