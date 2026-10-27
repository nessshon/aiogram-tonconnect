from aiogram import Router
from aiogram.dispatcher.event.telegram import TelegramEventObserver
from ton_connect import Event

from .events.dispatch import event_name


class TonConnectRouter(Router):
    """A ``Router`` with observers of the TON Connect events.

    Handlers get ``TonConnectEvent``, ``result`` (the wallet answer, ``None`` unless done) and ``wallet``;
    ``disconnect`` gets ``DisconnectEvent`` and ``wallet``.
    """

    def __init__(self, *, name: str | None = None) -> None:
        super().__init__(name=name)
        self.connect = self._observer(Event.CONNECT)
        self.transaction = self._observer(Event.TRANSACTION)
        self.sign_message = self._observer(Event.SIGN_MESSAGE)
        self.sign_data = self._observer(Event.SIGN_DATA)
        self.disconnect = self._observer(Event.DISCONNECT)

    def _observer(self, event: Event) -> TelegramEventObserver:
        name = event_name(event)
        # Middlewares are looked up by event name along the router chain, so the key must equal it
        observer = self.observers[name] = TelegramEventObserver(router=self, event_name=name)
        return observer
