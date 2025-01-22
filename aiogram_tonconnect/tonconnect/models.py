from dataclasses import dataclass
from typing import Awaitable, Callable, Optional, Any, Dict

from pytoniq_core import Address
from tonutils.tonconnect.models import WalletInfo, Account


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


@dataclass
class AccountWallet(Account):

    def to_dict(self) -> Dict[str, Any]:
        return {
            "address": self.address.to_str(is_bounceable=False),
            "network": self.chain.value,
            "walletStateInit": self.wallet_state_init,
            "publicKey": self.public_key,
        }


@dataclass
class InfoWallet(WalletInfo):

    def to_dict(self) -> Dict[str, Any]:
        account = self.account if self.account else None
        if account is not None:
            account["address"] = account["address"].to_str(is_bounceable=False)  # type: ignore

        ton_proof = self.ton_proof if self.ton_proof else None
        if ton_proof is not None:
            ton_proof["signature"] = ton_proof["signature"].hex()  # type: ignore

        return {
            "device": self.device,
            "provider": self.provider,
            "account": account,
            "ton_proof": ton_proof,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WalletInfo:
        data["account"]["address"] = Address(data["account"]["address"])
        data["ton_proof"]["signature"] = bytes.fromhex(data["ton_proof"]["signature"])
        return cls(**data)
