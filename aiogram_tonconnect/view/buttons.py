from aiogram.filters.callback_data import CallbackData


class GoBack(CallbackData, prefix="tonconnect_back"):
    """Ends the operation."""

    operation_id: str


class SelectWallet(CallbackData, prefix="tonconnect_wallet"):
    """Shows the connect links of a wallet."""

    operation_id: str
    app_name: str


class ShowWallets(CallbackData, prefix="tonconnect_wallets"):
    """Shows a page of the wallets with the ``tc://`` link."""

    operation_id: str
    page: int
