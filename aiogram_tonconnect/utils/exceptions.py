class AiogramTonconnectException(Exception):
    """
    Base exception class for Aiogram AiogramTonConnect custom exceptions.
    """


class RetrySendTransactionError(AiogramTonconnectException):
    """
    Exception raised when there is a need to retry sending a transaction.
    """


class RetryConnectWalletError(AiogramTonconnectException):
    """
    Exception raised when there is a need to retry connecting to a wallet.
    """


class LanguageCodeNotSupported(AiogramTonconnectException):
    """
    Exception raised when an unsupported language code is encountered.
    """


# List of error messages related to editing messages
MESSAGE_EDIT_ERRORS = [
    "no text in the message",
    "message can't be edited",
    "message is not modified",
    "message to edit not found",
]

# List of error messages related to deleting messages
MESSAGE_DELETE_ERRORS = [
    "message can't be deleted",
    "message to delete not found",
]
