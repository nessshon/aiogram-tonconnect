from enum import Enum
from typing import Awaitable, Callable, Dict, List, Optional, Any
from pydantic import BaseModel, Field

from aiogram_tonconnect.utils.address import Address


class AppWallet(BaseModel):
    """
    Data class representing a AiogramTonConnect application wallet.

    - app_name: Name of the application.
    - name: Name of the wallet.
    - image: URL of the wallet image.
    - bridge: List of dictionaries representing the bridge.
    - bridge_url: Optional URL of the bridge.
    - platforms: Optional list of supported platforms.
    - tondns: Optional TON DNS information.
    - about_url: Optional URL providing information about the wallet.
    - universal_url: Optional universal URL associated with the wallet.
    """

    app_name: str
    name: str
    image: str
    bridge: List[Dict]
    bridge_url: Optional[str] = Field(default=None)
    platforms: List[str] = Field(default=None)
    tondns: Optional[str] = Field(default=None)
    about_url: Optional[str] = Field(default=None)
    universal_url: Optional[str] = Field(default=None)


class AccountWallet(BaseModel):
    """
    Data class representing a AiogramTonConnect account wallet.

    - address: Optional wallet address.
    - state_init: Optional wallet state initialization.
    - public_key: Optional public key associated with the wallet.
    - chain: Optional chain information.
    """

    address: Optional[Address] = Field(default=None)
    state_init: Optional[str] = Field(default=None)
    public_key: Optional[str] = Field(default=None)
    chain: Optional[int] = Field(default=None)


class ATCUser(BaseModel):
    """
    Data class representing a AiogramTonConnect user.

    - id: User ID.
    - language_code: Language code associated with the user.
    - app_wallet: Optional AiogramTonConnect application wallet.
    - account_wallet: Optional AiogramTonConnect account wallet.
    - last_transaction_boc: Optional BOC of the last transaction.
    """

    id: int
    language_code: str
    app_wallet: Optional[AppWallet] = Field(default=None)
    account_wallet: Optional[AccountWallet] = Field(default=None)
    last_transaction_boc: Optional[str] = Field(default=None)


class TransactionMessage(BaseModel):
    """
    Data class representing a AiogramTonConnect transaction message.

    - address: Receiver's address.
    - amount: Amount to send in nanoTon.
    - stateInit (string base64, optional): raw once-cell BoC encoded in Base64.
    - payload (string base64, optional): raw one-cell BoC encoded in Base64.

    Example:
        A payload for a TON transfer with commentary:
        payload = urlsafe_b64encode(
            begin_cell()
            .store_uint(0, 32)
            .store_string(comment)
            .end_cell()
            .to_boc()
        ).decode()
    """

    address: str
    amount: str
    stateInit: Optional[str] = Field(default="")
    payload: Optional[str] = Field(default="")


class CHAIN(str, Enum):
    MAINNET = "-239"
    TESTNET = "-3"


class Transaction(BaseModel):
    """
    Data class representing a AiogramTonConnect transaction.

    - valid_until: Validity duration of the transaction.
    - network: The network (mainnet or testnet) where DApp intends to send the transaction.
    If not set, the transaction is sent to the network currently set in the wallet,
    but this is not safe and DApp should always strive to set the network.
    If the network parameter is set, but the wallet has a different network set,
    the wallet should show an alert and DO NOT ALLOW TO SEND this transaction.
    - from_: The sender address in '<wc>:<hex>' format from which DApp intends to send the transaction.
    Current account. address by default.
    - messages: List of transaction messages: min is 1, max is 4.
    """

    valid_until: int
    network: Optional[CHAIN] = Field(default=CHAIN.MAINNET.value)
    from_: Optional[str] = Field(default="", alias="from")
    messages: List[TransactionMessage]

    def model_dump(self, **kwargs) -> dict[str, Any]:
        data = super().model_dump(**kwargs)
        data["from"] = data.pop("from_")
        return data


class ConnectWalletCallbacks(BaseModel):
    """
    Data class representing callbacks for connecting a wallet.

    - before_callback: Callable function to be executed before connecting the wallet.
    - after_callback: Callable function to be executed after connecting the wallet.
    """

    before_callback: Callable[..., Awaitable]
    after_callback: Callable[..., Awaitable]


class SendTransactionCallbacks(BaseModel):
    """
    Data class representing callbacks for sending a transaction.

    - before_callback: Callable function to be executed before sending the transaction.
    - after_callback: Callable function to be executed after sending the transaction.
    """

    before_callback: Callable[..., Awaitable]
    after_callback: Callable[..., Awaitable]
