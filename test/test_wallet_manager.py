
import pytest

from aiogram_tonconnect.tonconnect.wallet.manager import WalletManager


@pytest.mark.asyncio
@pytest.mark.parametrize('wallets_order, expected_wallets', [
    ([], ['telegram-wallet', 'tonkeeper', 'mytonwallet', 'tonhub']),
    (['mytonwallet', 'tonkeeper'], ['mytonwallet', 'tonkeeper', 'telegram-wallet', 'tonhub']),
    (['tonhub'], ['tonhub', 'telegram-wallet', 'tonkeeper', 'mytonwallet']),
])
async def test_wallet_get_wallets(wallets_order, expected_wallets):
    wm = WalletManager(wallets_order=wallets_order)
    wallets = await wm.get_wallets()
    wallet_names = [wallet.app_name for wallet in wallets]
    assert wallet_names[:len(expected_wallets)] == expected_wallets


