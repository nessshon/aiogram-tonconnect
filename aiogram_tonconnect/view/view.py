from __future__ import annotations

import html
import math
import time
import typing as t
from contextlib import suppress
from dataclasses import dataclass
from urllib.parse import urlencode

from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LinkPreviewOptions, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .buttons import GoBack, SelectWallet, ShowWallets
from .texts import ButtonStyles, Texts

if t.TYPE_CHECKING:
    from aiogram import Bot
    from aiogram.types import User
    from ton_connect.models import AppWallet

    from ..core.models import Operation


@dataclass(frozen=True)
class Screen:
    """What a ``View`` method returns: the text of the message, its buttons and link preview."""

    text: str
    markup: InlineKeyboardMarkup
    preview: LinkPreviewOptions | None = None


class ScreenGone(Exception):
    """Raised by ``View.show`` when the message of the operation is deleted: the operation ends as by Back."""


class View:
    """Screens of the operations, shown in the message of the operation.

    Override ``language`` to pick the texts, ``qr_image_url`` to draw the QR code elsewhere, ``connect``, ``waiting``
    or ``error`` to change a screen, ``show`` and ``hide`` to show it elsewhere.
    Every screen needs a ``GoBack`` button: it is the only way out.

    :param texts: Texts by language code; a user gets theirs, or ``en``.
    :param styles: Styles of the buttons and icons of the wallets.
    :param wallets_per_page: Wallet buttons on a page of the connect screen, two in a row.
    """

    def __init__(
        self,
        texts: t.Mapping[str, Texts] | None = None,
        styles: ButtonStyles | None = None,
        wallets_per_page: int = 4,
    ) -> None:
        self.texts = dict(texts or {})
        self.styles = styles or ButtonStyles()
        self.wallets_per_page = wallets_per_page

    async def show_connect(
        self,
        bot: Bot,
        operation: Operation,
        wallets: list[AppWallet],
        selected: AppWallet | None,
        qr_link: str,
        open_link: str | None,
        page: int,
    ) -> Message:
        screen = await self.connect(operation, wallets, selected, qr_link, open_link, page)
        return await self.show(bot, operation, screen)

    async def show_waiting(
        self, bot: Bot, operation: Operation, wallet: AppWallet | None, open_link: str | None
    ) -> Message:
        return await self.show(bot, operation, await self.waiting(operation, wallet, open_link))

    async def show_error(self, bot: Bot, operation: Operation) -> Message:
        return await self.show(bot, operation, await self.error(operation))

    async def hide(self, bot: Bot, operation: Operation) -> None:
        """Remove the screen: the operation ended and no handler took it."""
        message = operation.message
        if message is None:
            return
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        except TelegramBadRequest as error:
            if "message to delete not found" in error.message:
                return
            # A bot cannot delete its messages older than 48 hours; the dead buttons are taken off instead, and if that
            # fails too, they only stay on an old message
            with suppress(TelegramBadRequest):
                await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=message.message_id)

    async def show(self, bot: Bot, operation: Operation, screen: Screen) -> Message:
        """Show a screen in the message of the operation, or in a new one; return the message now holding it."""
        preview = screen.preview or LinkPreviewOptions(is_disabled=True)
        if operation.message is not None:
            try:
                edited = await bot.edit_message_text(
                    text=screen.text,
                    chat_id=operation.message.chat.id,
                    message_id=operation.message.message_id,
                    parse_mode=ParseMode.HTML,
                    link_preview_options=preview,
                    reply_markup=screen.markup,
                )
                # Bot API answers True instead of the message only for inline messages, which a bot chat has none of
                return edited if isinstance(edited, Message) else operation.message
            except TelegramBadRequest as error:
                # Telegram tells these cases apart only by the text
                if "message is not modified" in error.message:
                    return operation.message
                if "message to edit not found" in error.message:
                    # The user or the bot deleted the screen: a new message would come out of nowhere
                    raise ScreenGone from error
        # The message is too old or not a text one: the screen moves to a new message. It is sent first, so a screen
        # Telegram refuses leaves the old message in place
        sent = await bot.send_message(
            chat_id=operation.user.id,
            text=screen.text,
            parse_mode=ParseMode.HTML,
            link_preview_options=preview,
            reply_markup=screen.markup,
        )
        await self.hide(bot, operation)
        return sent

    async def language(self, user: User) -> str | None:
        """Return the language of the user's screens; the one of Telegram by default."""
        return user.language_code

    async def texts_for(self, user: User) -> Texts:
        """Return the texts in the language of the user: ``pt-br`` falls back to ``pt``, then to ``en``."""
        language = await self.language(user) or ""
        return self.texts.get(language) or self.texts.get(language.split("-")[0]) or self.texts.get("en") or Texts()

    async def qr_image_url(self, link: str, wallet: AppWallet | None) -> str:
        """Return a public URL of the QR image of ``link``; ``wallet`` is ``None`` for the ``tc://`` link.

        The image is drawn by qrcode.ness.uz with the wallet icon in the middle; the link goes to that service.
        """
        query = {"data": link, "size": "large", "style": "rounded"}
        if wallet is not None:
            query["logo"] = wallet.image
        return f"https://qrcode.ness.uz/create?{urlencode(query)}"

    async def connect(
        self,
        operation: Operation,
        wallets: list[AppWallet],
        selected: AppWallet | None,
        qr_link: str,
        open_link: str | None,
        page: int,
    ) -> Screen:
        texts = await self.texts_for(operation.user)
        size = self.wallets_per_page
        pages = max(math.ceil(len(wallets) / size), 1)
        chosen = selected.app_name if selected is not None else None
        if chosen is not None:
            page = next((i for i, wallet in enumerate(wallets) if wallet.app_name == chosen), 0) // size
        page %= pages
        keyboard = InlineKeyboardBuilder()
        # A button URL must be http(s) or tg://, so the tc:// link of no wallet in particular lives only in the QR code
        if selected is not None and open_link is not None:
            keyboard.row(self._open_wallet(texts, selected.name, open_link))
        shown = wallets[page * size : (page + 1) * size]
        keyboard.row(*(self._wallet(operation, wallet, page, wallet.app_name == chosen) for wallet in shown), width=2)
        if pages > 1:
            keyboard.row(*(self._page(operation, text, target) for text, target in _pager(page, pages)))
        keyboard.row(self._go_back(texts, operation))
        # Names come from the wallet catalog, and the texts are HTML
        wallet_name = html.escape(selected.name) if selected is not None else texts.unknown_wallet
        text = texts.connect.format(wallet_name=wallet_name, minutes=_minutes_left(operation))
        # Every field is set: aiogram fills the ones left out from the bot defaults, and link_preview_is_disabled
        # there would hide the QR code
        preview = LinkPreviewOptions(
            is_disabled=False,
            url=await self.qr_image_url(qr_link, selected),
            prefer_small_media=False,
            prefer_large_media=True,
            show_above_text=True,
        )
        return Screen(text, keyboard.as_markup(), preview)

    async def waiting(self, operation: Operation, wallet: AppWallet | None, open_link: str | None) -> Screen:
        texts = await self.texts_for(operation.user)
        wallet_name = wallet.name if wallet is not None else texts.unknown_wallet
        rows = [[self._go_back(texts, operation)]]
        if open_link is not None:
            rows.insert(0, [self._open_wallet(texts, wallet_name, open_link)])
        # The fields of Texts are named after the values of OperationKind
        template = getattr(texts, f"confirm_{operation.kind.value}")
        text_name = html.escape(wallet.name) if wallet is not None else texts.unknown_wallet
        text = template.format(wallet_name=text_name, minutes=_minutes_left(operation))
        return Screen(text, InlineKeyboardMarkup(inline_keyboard=rows))

    async def error(self, operation: Operation) -> Screen:
        texts = await self.texts_for(operation.user)
        # The fields of Texts are named after the values of ErrorKind
        text = getattr(texts, operation.error.value if operation.error is not None else "failed")
        return Screen(text, InlineKeyboardMarkup(inline_keyboard=[[self._go_back(texts, operation)]]))

    def _open_wallet(self, texts: Texts, wallet_name: str, url: str) -> InlineKeyboardButton:
        text = texts.open_wallet.format(wallet_name=wallet_name)
        return InlineKeyboardButton(text=text, url=url, style=self.styles.open_wallet)

    def _wallet(self, operation: Operation, wallet: AppWallet, page: int, highlighted: bool) -> InlineKeyboardButton:
        # The selected wallet unselects itself: the page comes back with the tc:// link
        action: SelectWallet | ShowWallets = (
            ShowWallets(operation_id=operation.id, page=page)
            if highlighted
            else SelectWallet(operation_id=operation.id, app_name=wallet.app_name)
        )
        return InlineKeyboardButton(
            text=_current(wallet.name) if highlighted else wallet.name,
            callback_data=action.pack(),
            style=self.styles.selected_wallet if highlighted else None,
            icon_custom_emoji_id=self.styles.wallet_icons.get(wallet.app_name),
        )

    @staticmethod
    def _page(operation: Operation, text: str, page: int) -> InlineKeyboardButton:
        return InlineKeyboardButton(text=text, callback_data=ShowWallets(operation_id=operation.id, page=page).pack())

    def _go_back(self, texts: Texts, operation: Operation) -> InlineKeyboardButton:
        action = GoBack(operation_id=operation.id)
        return InlineKeyboardButton(text=texts.go_back, callback_data=action.pack(), style=self.styles.go_back)


def _pager(page: int, pages: int) -> list[tuple[str, int]]:
    """Return the page buttons, at most five: ``« 1  ‹ 3  · 4 ·  5 ›  8 »``."""
    if pages <= 5:
        targets = list(range(pages))
        prefixes = suffixes = ("",) * pages
    else:
        start, end = page < 3, page > pages - 4
        if start:
            targets = [0, 1, 2, 3, pages - 1]
        elif end:
            targets = [0, pages - 4, pages - 3, pages - 2, pages - 1]
        else:
            targets = [0, page - 1, page, page + 1, pages - 1]
        prefixes = ("" if start else "« ", "" if start else "‹ ", "", "", "")
        suffixes = ("", "", "", "" if end else " ›", "" if end else " »")
    return [
        (_current(str(target + 1)) if target == page else f"{prefix}{target + 1}{suffix}", target)
        for target, prefix, suffix in zip(targets, prefixes, suffixes, strict=True)
    ]


def _current(text: str) -> str:
    return f"· {text} ·"


def _minutes_left(operation: Operation) -> int:
    return math.ceil(max(operation.deadline - time.time(), 0) / 60)
