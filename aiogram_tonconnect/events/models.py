from enum import Enum

from aiogram.types import Message, TelegramObject
from nacl.exceptions import BadSignatureError
from pydantic import ConfigDict
from ton_connect.exceptions import (
    BridgeUnreachableError,
    ManifestContentError,
    ManifestNotFoundError,
    MethodNotSupportedError,
    RequestTimeoutError,
    UnknownAppError,
    UserRejectsError,
    WalletMissingRequiredFeaturesError,
    WalletNotConnectedError,
    WalletNotSupportFeatureError,
    WalletWrongNetworkError,
)


class ErrorKind(str, Enum):
    """Why an operation failed, from the ``ton_connect`` error behind it."""

    REJECTED = "rejected"
    TIMEOUT = "timeout"
    WRONG_NETWORK = "wrong_network"
    BAD_SIGNATURE = "bad_signature"
    BAD_MANIFEST = "bad_manifest"
    NOT_SUPPORTED = "not_supported"
    NOT_CONNECTED = "not_connected"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"

    @classmethod
    def of(cls, error: Exception) -> "ErrorKind":
        """Classify a ``ton_connect`` error or a failed signature check."""
        if isinstance(error, UserRejectsError):
            return cls.REJECTED
        if isinstance(error, RequestTimeoutError):
            return cls.TIMEOUT
        if isinstance(error, WalletWrongNetworkError):
            return cls.WRONG_NETWORK
        if isinstance(error, BadSignatureError):
            return cls.BAD_SIGNATURE
        if isinstance(error, (ManifestNotFoundError, ManifestContentError)):
            return cls.BAD_MANIFEST
        if isinstance(
            error,
            (
                WalletNotSupportFeatureError,
                WalletMissingRequiredFeaturesError,
                MethodNotSupportedError,
            ),
        ):
            return cls.NOT_SUPPORTED
        if isinstance(error, (WalletNotConnectedError, UnknownAppError)):
            return cls.NOT_CONNECTED
        if isinstance(error, BridgeUnreachableError):
            return cls.UNAVAILABLE
        return cls.FAILED


class Status(str, Enum):
    """How an operation ended."""

    DONE = "done"
    """The wallet approved the request."""
    CANCELLED = "cancelled"
    """The user left before the bot took the answer of the wallet; a transaction may still be sent, check the chain."""
    FAILED = "failed"
    """The operation did not complete; ``error`` tells why."""


class TonConnectEvent(TelegramObject):
    """End of an operation, passed to the handlers of its kind."""

    # TelegramObject keeps the values of enums; status and error stay Status and ErrorKind
    model_config = ConfigDict(use_enum_values=False)

    id: str | None
    """The operation ID ``tc`` returned; ``None`` for a connection."""
    payload: str | None
    """Given to the ``tc`` call that started the operation."""
    status: Status
    error: ErrorKind | None = None
    message: Message
    """The message with the screen: a handler may edit it, or it is removed when no handler takes the event."""


class DisconnectEvent(TelegramObject):
    """The wallet is disconnected by ``tc.disconnect``; a disconnect in the wallet only makes ``tc.wallet`` ``None``."""

    payload: str | None = None
    """Given to ``tc.disconnect``."""
    message: Message
    """The message ``tc.disconnect`` was called from."""
