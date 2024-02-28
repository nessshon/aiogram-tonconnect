from enum import IntEnum
from typing import Awaitable, Callable, Dict, List, Optional, Any, Union

from pydantic import BaseModel, Field
from pytonconnect.parsers import WalletInfo

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


class DeviceInfo(BaseModel):
    """
    Data class representing a device information.

    - platform: Device platform (e.g. "iphone" | "ipad" | "android").
    - app_name: Application name (e.g. "Tonkeeper").
    - app_version: Application version (e.g. "2.3.367").
    - max_protocol_version: Maximum protocol version supported by the device.
    - features: List of device features.
    """
    platform: str
    app_name: str
    app_version: str
    max_protocol_version: int
    features: List[Union[dict, str]]


class TonProof(BaseModel):
    """
    Data class representing a TON Proof.

    - timestamp: Timestamp of the proof.
    - domain_len: Length of the domain.
    - domain_val: Domain value.
    - payload: Payload of the proof.
    - signature: Signature of the proof.
    """
    timestamp: int
    domain_len: int
    domain_val: str
    payload: str
    signature: str


class InfoWallet(BaseModel):
    """
    Data class representing information about user's wallet.

    - device: Information about user's wallet's device.
    - provider: Provider type.
    - account: Selected account.
    - ton_proof: Response for ton_proof item request.
    """
    device: Optional[DeviceInfo] = Field(default=None)
    provider: Optional[str] = Field(default="http")
    account: Optional[AccountWallet] = Field(default=None)
    ton_proof: Optional[TonProof] = Field(default=None)

    @staticmethod
    def from_pytonconnect_wallet(wallet: WalletInfo) -> 'InfoWallet':
        return InfoWallet(
            device=DeviceInfo(
                platform=wallet.device.platform,
                app_name=wallet.device.app_name,
                app_version=wallet.device.app_version,
                max_protocol_version=wallet.device.max_protocol_version,
                features=wallet.device.features,
            ) if wallet.device else None,
            provider=wallet.provider,
            account=AccountWallet(
                address=Address(hex_address=wallet.account.address),
                state_init=wallet.account.wallet_state_init,
                public_key=wallet.account.public_key,
                chain=wallet.account.chain,
            ) if wallet.account else None,
            ton_proof=TonProof(
                timestamp=wallet.ton_proof.timestamp,
                domain_len=wallet.ton_proof.domain_len,
                domain_val=wallet.ton_proof.domain_val,
                payload=wallet.ton_proof.payload,
                signature=wallet.ton_proof.signature.hex(),
            ) if wallet.ton_proof else None,
        )


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
    info_wallet: Optional[InfoWallet] = Field(default=None)
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


class CHAIN(IntEnum):
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
