from typing import List, Optional

from pytonconnect import TonConnect as BaseTonConnect
from pytonconnect.storage import IStorage
from pytonconnect.logger import _LOGGER  # noqa

from .provider import BridgeProvider
from .wallet.manager import WalletManager
from .models import AppWallet


class AiogramTonConnect(BaseTonConnect):
    """
    AiogramTonConnect class that extends the base AiogramTonConnect functionality.

    :param storage: An instance of IStorage for data storage.
    :param manifest_url: URL to the manifest file.
    :param redirect_url: URL to the redirect after connecting.
    :param exclude_wallets: Optional list of wallet names to exclude.
    :param args: Additional positional arguments.
    :param kwargs: Additional keyword arguments.
    """

    def __init__(
            self,
            storage: IStorage,
            manifest_url: str,
            redirect_url: str = None,
            exclude_wallets: Optional[List[str]] = None,
            *args,
            **kwargs,
    ) -> None:
        """
        Initialize AiogramTonConnect.

        :param storage: An instance of IStorage for data storage.
        :param manifest_url: URL to the manifest file.
        :param redirect_url: URL to the redirect after connecting.
        :param exclude_wallets: Optional list of wallet names to exclude.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        """
        kwargs["storage"] = storage
        kwargs["manifest_url"] = manifest_url
        super().__init__(*args, **kwargs)
        self.redirect_url = redirect_url
        self.wallet_manager = WalletManager(exclude_wallets=exclude_wallets)

    async def get_wallets(self=None) -> List[AppWallet]:
        """
        Get the list of AiogramTonConnect wallets.

        :return: List of AiogramTonConnect application wallet instances.
        """
        return await self.wallet_manager.get_wallets()

    def _create_provider(self, wallet: dict) -> BridgeProvider:
        provider = BridgeProvider(self._storage, wallet, redirect_url=self.redirect_url)
        provider.listen(self._wallet_events_listener)
        return provider
