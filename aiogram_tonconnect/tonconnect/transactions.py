import time
from base64 import urlsafe_b64encode
from typing import Optional

from pytoniq_core import begin_cell

from .models import Transaction, TransactionMessage

__all__ = [
    "TONTransferTransaction",
    "NFTTransferTransaction",
]


class TONTransferTransaction(Transaction):
    """
    Create a TON (Telegram Open Network) transfer transaction.

    :param address: The address to which the transfer is made.
    :param amount: The amount to be transferred.
    :param comment: An optional comment for the transaction.
    """

    def __init__(
            self,
            address: str,
            amount: str,
            comment: Optional[str] = "",
    ) -> None:
        payload = urlsafe_b64encode(
            begin_cell()
            .store_uint(0, 32)
            .store_string(comment)
            .end_cell()
            .to_boc()
        ).decode()
        super().__init__(
            messages=[
                TransactionMessage(
                    address=address,
                    payload=payload,
                    amount=amount,
                ),
            ],
            valid_until=int(time.time() + 300),
        )


class JettonTransferTransaction(Transaction):
    """
    Create a Jetton transfer transaction.

    :param jetton_wallet_address: The address of the Jetton wallet.
    :param recipient_address: The recipient's address.
    :param jetton_amount: The amount of Jetton to transfer.
    :param jetton_decimal: The number of decimal places in the Jetton amount (default is 9).
    :param response_address: The address for the response (default is the recipient's address).
    """

    def __init__(
            self,
            jetton_wallet_address: str,
            recipient_address: str,
            jetton_amount: int,
            jetton_decimal: int = 9,
            response_address: str = None,
    ) -> None:
        payload = urlsafe_b64encode(
            begin_cell()
            .store_uint(0xf8a7ea5, 32)
            .store_uint(0, 64)
            .store_coins(int(jetton_amount * 10 ** jetton_decimal))
            .store_address(recipient_address)
            .store_address(response_address or recipient_address)
            .store_uint(0, 1)
            .store_coins(1)
            .store_uint(0, 1)
            .end_cell()
            .to_boc()
        ).decode()
        super().__init__(
            messages=[
                TransactionMessage(
                    address=jetton_wallet_address,
                    payload=payload,
                    amount=str(int(0.07 * 10 ** 9)),
                ),
            ],
            valid_until=int(time.time() + 300),
        )


class NFTTransferTransaction(Transaction):
    """
    Create an NFT (Non-Fungible Token) transfer transaction.

    :param nft_address: The address of the NFT.
    :param recipient_address: The recipient's address.
    :param response_address: The address for the response (default is the recipient's address).
    :param transfer_fee: The transfer fee amount (default is 0.05 TON).
    """

    def __init__(
            self,
            nft_address: str,
            recipient_address: str,
            response_address: str = None,
            transfer_fee: str = str(int(0.05 * 10 ** 9)),
    ) -> None:
        payload = urlsafe_b64encode(
            begin_cell()
            .store_uint(0x5fcc3d14, 32)
            .store_uint(0, 64)
            .store_address(recipient_address)
            .store_address(response_address or recipient_address)
            .store_uint(0, 1)
            .store_coins(1)
            .store_uint(0, 1)
            .end_cell()
            .to_boc()
        ).decode()
        super().__init__(
            messages=[
                TransactionMessage(
                    address=nft_address,
                    payload=payload,
                    amount=transfer_fee,
                ),
            ],
            valid_until=int(time.time() + 300),
        )
