from dataclasses import dataclass
from typing import Awaitable, Callable, Optional, Any, Dict

from pytoniq_core import Address


@dataclass
class ConnectWalletCallbacks:
    """
    Data class representing callbacks for connecting a wallet.

    - before_callback: Callable function to be executed before connecting the wallet.
    - after_callback: Callable function to be executed after connecting the wallet.
    """

    before_callback: Callable[..., Awaitable]
    after_callback: Callable[..., Awaitable]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "before_callback": self.before_callback,
            "after_callback": self.after_callback,
        }


@dataclass
class SendTransactionCallbacks:
    """
    Data class representing callbacks for sending a transaction.

    - before_callback: Callable function to be executed before sending the transaction.
    - after_callback: Callable function to be executed after sending the transaction.
    """

    before_callback: Callable[..., Awaitable]
    after_callback: Callable[..., Awaitable]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "before_callback": self.before_callback,
            "after_callback": self.after_callback,
        }


@dataclass
class ATCUser:
    id: int
    wallet_address: Address
    language_code: Optional[str] = None
    last_transaction_boc: Optional[str] = None
    last_normalized_hash: Optional[str] = None
