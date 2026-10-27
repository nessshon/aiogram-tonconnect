import typing as t
from enum import Enum

from aiogram.filters.callback_data import CallbackData
from aiogram.types import Message, User
from pydantic import BaseModel, field_serializer
from ton_connect import Event

from ..events.models import ErrorKind


def pack_payload(payload: str | CallbackData | None) -> str | None:
    return payload.pack() if isinstance(payload, CallbackData) else payload


class OperationKind(str, Enum):
    CONNECT = "connect"
    TRANSACTION = "transaction"
    SIGN_MESSAGE = "sign_message"
    SIGN_DATA = "sign_data"

    @property
    def event(self) -> Event:
        """The ``ton_connect`` event that ends the operation."""
        return Event(self.value)


class Operation(BaseModel):
    """A request to the wallet, stored until it ends; views draw its screens."""

    id: str
    kind: OperationKind
    user: User
    message: Message | None = None
    request_id: int | None = None
    session_id: str | None = None
    payload: str | None = None
    error: ErrorKind | None = None
    deadline: int = 0

    @field_serializer("message")
    def _dump_message(self, message: Message | None) -> dict[str, t.Any] | None:
        # aiogram fills the fields the Bot API left out with Default, which has no JSON form
        return message.model_dump(mode="json", exclude_unset=True) if message is not None else None
