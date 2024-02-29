import time
from base64 import urlsafe_b64encode
from typing import Optional, Union

from pytoniq_core import begin_cell, Cell

from .models import Transaction, TransactionMessage

__all__ = [
    "TONTransferTransaction",
    "JettonTransferTransaction",
    "NFTTransferTransaction",
]


class TONTransferTransaction(Transaction):
    """
    Create a TON (Telegram Open Network) transfer transaction.

    :param address: The address to which the transfer is made.
    :param amount: The amount in TON to be transferred.
    :param comment: An optional comment for the transaction.
    """

    def __init__(
            self,
            address: str,
            amount: Union[int, float],
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
                    amount=str(int(amount * 1e9)),
                ),
            ],
            valid_until=int(time.time() + 300),
        )


class JettonTransferTransaction(Transaction):
    """
    Create a Jetton transfer transaction.
    Jetton specification link https://github.com/ton-blockchain/TEPs/blob/master/text/0074-jettons-standard.md

    :param jetton_wallet_address: The address of the Jetton wallet.
    :param recipient_address: The recipient's address.
    :param jetton_amount: The amount of Jetton to transfer.
    :param jetton_decimal: The number of decimal places in the Jetton amount (default is 9).
    :param query_id: The query ID (default is 0).
    :param transfer_fee: The transfer fee amount in TON (default is 0.05 TON).
    :param response_address: The address for the response (the sender's address is specified).
        If the address is specified, the excess of TON is returned to the specified address;
        otherwise, it remains on the token contract.
    :param custom_payload: Custom payload for the transaction.
    :param forward_payload: Forward payload for the transaction.
        If forward_amount is greater than 0, this payload will be included with the notification to the new owner.
    :param forward_amount: Forward amount in TON (default is 0.01 TON).
        A notification will be sent to the new owner if the amount is greater than 0;
        otherwise, the new owner will not receive a notification.
    """

    def __init__(
            self,
            jetton_wallet_address: str,
            recipient_address: str,
            jetton_amount: int,
            jetton_decimal: int = 9,
            query_id: Optional[int] = 0,
            transfer_fee: Union[float, int] = 0.05,
            response_address: Optional[str] = None,
            custom_payload: Optional[Cell] = Cell.empty(),
            forward_payload: Optional[Cell] = Cell.empty(),
            forward_amount: Union[float, int] = 0.01,
    ) -> None:
        payload = urlsafe_b64encode(
            begin_cell()
            .store_uint(0xf8a7ea5, 32)
            .store_uint(query_id, 64)
            .store_coins(int(jetton_amount * 10 ** jetton_decimal))
            .store_address(recipient_address)
            .store_address(response_address)
            .store_maybe_ref(custom_payload)
            .store_coins(int(forward_amount * 1e9))
            .store_maybe_ref(forward_payload)
            .end_cell()
            .to_boc()
        ).decode()
        super().__init__(
            messages=[
                TransactionMessage(
                    address=jetton_wallet_address,
                    payload=payload,
                    amount=str(int(transfer_fee * 1e9)),
                ),
            ],
            valid_until=int(time.time() + 300),
        )


class NFTTransferTransaction(Transaction):
    """
    Create an NFT (Non-Fungible Token) transfer transaction.
    Link to NFT specification https://github.com/ton-blockchain/TEPs/blob/master/text/0062-nft-standard.md

    :param nft_address: The address of the NFT.
    :param new_owner_address: The new owner address.
    :param response_address: The address for the response (the sender's address is specified).
        If the address is specified, the excess of TON is returned to the specified address;
        otherwise, it remains on the token contract.
    :param query_id: The query ID (default is 0).
    :param transfer_fee: The transfer fee amount (default is 0.05 TON).
    :param custom_payload: Custom payload for the transaction.
    :param forward_payload: Forward payload for the transaction.
        If forward_amount is greater than 0, this payload will be included with the notification to the new owner.
    :param forward_amount: Forward amount in TON (default is 0.01 TON).
        A notification will be sent to the new owner if the amount is greater than 0;
        otherwise, the new owner will not receive a notification.
    """

    def __init__(
            self,
            nft_address: str,
            new_owner_address: str,
            response_address: Optional[str] = None,
            query_id: Optional[int] = 0,
            transfer_fee: Union[int, float] = 0.05,
            custom_payload: Optional[Cell] = Cell.empty(),
            forward_payload: Optional[Cell] = Cell.empty(),
            forward_amount: Union[float, int] = 0.01,
    ) -> None:
        payload = urlsafe_b64encode(
            begin_cell()
            .store_uint(0x5fcc3d14, 32)
            .store_uint(query_id, 64)
            .store_address(new_owner_address)
            .store_address(response_address)
            .store_maybe_ref(custom_payload)
            .store_coins(int(forward_amount * 1e9))
            .store_maybe_ref(forward_payload)
            .end_cell()
            .to_boc()
        ).decode()
        super().__init__(
            messages=[
                TransactionMessage(
                    address=nft_address,
                    payload=payload,
                    amount=str(int(transfer_fee * 1e9)),
                ),
            ],
            valid_until=int(time.time() + 300),
        )
