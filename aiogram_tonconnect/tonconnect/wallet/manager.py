import json
from pathlib import Path
from typing import Any, Dict, List, Union

import aiofiles
from aiogram.client.session import aiohttp
from cachetools import TTLCache
from pytonconnect.exceptions import FetchWalletsError

from ..models import AppWallet


class _FallbackWalletManager:
    """
    Manager class for handling fallback wallets from a local file.
    """

    BASE_DIR = Path(__file__).parent

    def __init__(self, file_path: Union[str, Path] = None) -> None:
        """
        Initialize the FallbackWalletManager.

        :param file_path: Optional path to the fallback wallets file.
        """
        if file_path is None:
            file_path = self.BASE_DIR / 'wallets_fallback.json'
        self.file_path = file_path

    async def get_wallets(self) -> List[Dict[str, Any]]:
        """
        Retrieve wallets from the fallback file.

        :return: List of dictionaries representing wallets.
        """
        async with aiofiles.open(self.file_path, 'r') as f:
            return json.loads(await f.read())

    async def save_wallets(self, wallets: List[Dict[str, Any]]) -> None:
        """
        Save wallets to the fallback file.

        :param wallets: List of dictionaries representing wallets.
        """
        async with aiofiles.open(self.file_path, 'w') as f:
            await f.write(json.dumps(wallets))


class _CachedWalletManager:
    """
    Manager class for handling cached wallets with a TTL cache.
    """

    def __init__(self, cache_ttl: int = None) -> None:
        """
        Initialize the CachedWalletManager.

        :param cache_ttl: Time-to-live for the cache, in seconds.
        """
        if cache_ttl is None:
            cache_ttl = 86400
        self.cache = TTLCache(maxsize=1, ttl=cache_ttl)

    async def get_wallets(self) -> List[Dict[str, Any]]:
        """
        Retrieve wallets from the cache.

        :return: List of dictionaries representing wallets.
        """
        return self.cache.get("wallets")

    async def save_wallets(self, wallets: List[Dict[str, Any]]) -> None:
        """
        Save wallets to the cache.

        :param wallets: List of dictionaries representing wallets.
        """
        self.cache.setdefault("wallets", wallets)


class WalletManager:
    """
    Manager class for handling AiogramTonConnect wallets.

    :param wallets_list_source_url: URL to fetch the wallets list.
    :param exclude_wallets: List of wallet names to exclude.
    :param cache_ttl: Time-to-live for the cache, in seconds.
    :param file_path: Path to the fallback wallets file.
    """

    def __init__(
            self,
            wallets_list_source_url: str =
            'https://raw.githubusercontent.com/ton-blockchain/wallets-list/main/wallets-v2.json',
            exclude_wallets: List[str] = None,
            cache_ttl: int = None,
            file_path: str = None,
    ) -> None:
        """
        Initialize the WalletManager.

        :param wallets_list_source_url: URL to fetch the wallets list.
        :param exclude_wallets: List of wallet names to exclude.
        :param cache_ttl: Time-to-live for the cache, in seconds.
        :param file_path: Path to the fallback wallets file.
        """
        self.cache_manager = _CachedWalletManager(cache_ttl)
        self.fallback_manager = _FallbackWalletManager(file_path)

        self._exclude_wallets = exclude_wallets
        self._wallets_list_source_url = wallets_list_source_url

    async def __fetch(self) -> List[Dict[str, Any]]:
        """
        Fetch the wallets list from the specified URL.

        :return: List of dictionaries representing wallets.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(self._wallets_list_source_url) as response:
                if response.status == 200:
                    wallets = await response.json(content_type=response.content_type)
                    if not isinstance(wallets, list):
                        raise FetchWalletsError('Wrong wallets list format, wallets list must be an array.')
                    return wallets
                raise FetchWalletsError('Error fetching wallets')

    def __exclude(self, wallets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Exclude specified wallets from the list.

        :param wallets: List of dictionaries representing wallets.
        :return: List of dictionaries representing wallets after exclusion.
        """
        if self._exclude_wallets is None:
            return wallets
        return [w for w in wallets if w['app_name'] not in self._exclude_wallets]

    @staticmethod
    def __get_supported(wallets: List[Dict[str, Any]]) -> List[Dict]:
        """
        Filter out wallets that do not support the required features.

        :param wallets: List of dictionaries representing wallets.
        :return: List of dictionaries representing supported wallets.
        """
        supported_wallets = []
        for wallet in wallets:
            try:
                wallet_obj = AppWallet(**wallet)
            except (Exception,):
                continue
            for bridge in wallet_obj.bridge:
                if "sse" in bridge.get("type", "") and "url" in bridge:
                    wallet["bridge_url"] = bridge["url"]
                    supported_wallets.append(wallet)
                    break
        return supported_wallets

    async def __save_wallets(self, wallets: List[Dict[str, Any]]) -> None:
        await self.cache_manager.save_wallets(wallets)
        await self.fallback_manager.save_wallets(wallets)

    def __process_wallets(self, wallets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        excluded_wallets = self.__exclude(wallets)
        supported_wallets = self.__get_supported(excluded_wallets)
        return supported_wallets

    async def get_wallets(self) -> List[AppWallet]:
        """
        Get the list of AiogramTonConnect wallets.

        :return: List of AiogramTonConnect application wallet instances.
        """
        cached_wallets = await self.cache_manager.get_wallets()

        if cached_wallets:
            supported_wallets = self.__process_wallets(cached_wallets)
            return [AppWallet(**w) for w in supported_wallets]
        try:
            default_wallets = await self.__fetch()
        except (Exception,):
            default_wallets = await self.fallback_manager.get_wallets()

        supported_wallets = self.__process_wallets(default_wallets)
        await self.__save_wallets(default_wallets)
        return [AppWallet(**w) for w in supported_wallets]
