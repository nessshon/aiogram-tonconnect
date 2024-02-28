from aiogram.fsm.state import StatesGroup, State


class TcState(StatesGroup):
    """
    States group for managing different states in the AiogramTonConnect bot.

    States:
    - connect_wallet: State representing the process of connecting a wallet.
    - connect_wallet_timeout: State representing the timeout during the connection of a wallet.
    - connect_wallet_proof_wrong: State representing the proof of wrong during the connection of a wallet.
    - send_transaction: State representing the process of sending a transaction.
    - send_transaction_timeout: State representing the timeout during the sending of a transaction.
    - send_transaction_rejected: State representing the rejection of a transaction.
    """
    connect_wallet = State()
    connect_wallet_timeout = State()
    connect_wallet_proof_wrong = State()
    send_transaction = State()
    send_transaction_timeout = State()
    send_transaction_rejected = State()
