from dataclasses import dataclass, asdict
from typing import Awaitable, Callable, Dict, List, Optional


@dataclass
class Base:
    """
    Base data class providing a method to convert the instance to a dictionary.
    """

    def to_dict(self) -> Dict:
        """
        Convert the instance to a dictionary.

        :return: Dictionary representation of the instance.
        """
        return asdict(self)


@dataclass
class AppWallet(Base):
    """
    Data class representing a AiogramTonConnect application wallet.

    :param app_name: Name of the application.
    :param name: Name of the wallet.
    :param image: URL of the wallet image.
    :param bridge: List of dictionaries representing the bridge.
    :param bridge_url: Optional URL of the bridge.
    :param platforms: Optional list of supported platforms.
    :param tondns: Optional TON DNS information.
    :param about_url: Optional URL providing information about the wallet.
    :param universal_url: Optional universal URL associated with the wallet.
    """

    app_name: str
    name: str
    image: str
    bridge: List[Dict]
    bridge_url: Optional[str] = None
    platforms: List[str] = None
    tondns: Optional[str] = None
    about_url: Optional[str] = None
    universal_url: Optional[str] = None


@dataclass
class AccountWallet(Base):
    """
    Data class representing a AiogramTonConnect account wallet.

    :param address: Optional wallet address.
    :param state_init: Optional wallet state initialization.
    :param public_key: Optional public key associated with the wallet.
    :param chain: Optional chain information.
    """

    address: Optional[str] = None
    state_init: Optional[str] = None
    public_key: Optional[str] = None
    chain: Optional[int] = None


@dataclass
class ATCUser(Base):
    """
    Data class representing a AiogramTonConnect user.

    :param id: User ID.
    :param language_code: Language code associated with the user.
    :param app_wallet: Optional AiogramTonConnect application wallet.
    :param account_wallet: Optional AiogramTonConnect account wallet.
    :param last_transaction_boc: Optional BOC of the last transaction.
    """

    id: int
    language_code: str
    app_wallet: Optional[AppWallet] = None
    account_wallet: Optional[AccountWallet] = None
    last_transaction_boc: Optional[str] = None


@dataclass
class TransactionMessage(Base):
    """
    Data class representing a AiogramTonConnect transaction message.

    :param address: Wallet address associated with the message.
    :param payload: Payload of the message.
    :param amount: Amount associated with the message.
    """

    address: str
    payload: str
    amount: str


@dataclass
class Transaction(Base):
    """
    Data class representing a AiogramTonConnect transaction.

    :param valid_until: Validity duration of the transaction.
    :param messages: List of transaction messages.
    """

    valid_until: int
    messages: List[TransactionMessage]


@dataclass
class ConnectWalletCallbacks(Base):
    """
    Data class representing callbacks for connecting a wallet.

    :param before_callback: Callable function to be executed before connecting the wallet.
    :param after_callback: Callable function to be executed after connecting the wallet.
    """

    before_callback: Callable[[...], Awaitable]
    after_callback: Callable[[...], Awaitable]


@dataclass
class SendTransactionCallbacks(Base):
    """
    Data class representing callbacks for sending a transaction.

    :param before_callback: Callable function to be executed before sending the transaction.
    :param after_callback: Callable function to be executed after sending the transaction.
    """

    before_callback: Callable[[...], Awaitable]
    after_callback: Callable[[...], Awaitable]
