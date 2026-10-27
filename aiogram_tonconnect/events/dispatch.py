import logging
import typing as t

from aiogram import Bot, Dispatcher
from aiogram.dispatcher.event.bases import UNHANDLED
from aiogram.enums import ChatType
from aiogram.types import Chat, Update, User
from ton_connect import Event

from .models import DisconnectEvent, TonConnectEvent

logger = logging.getLogger(__name__)


class TonConnectUpdate(Update):
    """A TON Connect event as an update, so the bot middlewares see it; ``update_id`` is 0."""

    tonconnect_name: str
    tonconnect_event: TonConnectEvent | DisconnectEvent

    def __init__(self, name: str, event: TonConnectEvent | DisconnectEvent) -> None:
        super().__init__(update_id=0, tonconnect_name=name, tonconnect_event=event)

    @property
    def event_type(self) -> str:
        # Update caches its own by (type, update_id), which is the same for every TON Connect event
        return self.tonconnect_name

    @property
    def event(self) -> TonConnectEvent | DisconnectEvent:
        return self.tonconnect_event


def event_name(event: Event) -> str:
    # The prefix keeps the names apart from Telegram update types. Event is a str Enum: since Python 3.12 an f-string
    # gives "Event.CONNECT" for it, not the value
    return f"tonconnect_{event.value}"


async def propagate(
    dispatcher: Dispatcher, bot: Bot, user: User, update: TonConnectUpdate, data: dict[str, t.Any]
) -> bool:
    """Pass a TON Connect event through the dispatcher; a failed handler goes to ``dp.errors``.

    :return: Whether a handler took the event; a failed one counts as taken.
    """
    kwargs = {**data, "bot": bot, "event_from_user": user, "event_chat": Chat(id=user.id, type=ChatType.PRIVATE)}
    try:
        result = await dispatcher.propagate_event(update_type="update", event=update, **kwargs)
    except Exception:
        # Not handled in dp.errors either; the answer of the wallet came from the bridge, so there is no one to raise to
        logger.exception("Handler of %s failed for %s:%s", update.event_type, bot.id, user.id)
        return True
    return result is not UNHANDLED
