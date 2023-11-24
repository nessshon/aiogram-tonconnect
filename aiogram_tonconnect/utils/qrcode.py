import base64
from abc import ABCMeta, abstractmethod


class QRCodeProviderBase(metaclass=ABCMeta):
    """
    Abstract base class for QR code providers.

    Subclasses must implement the 'create_connect_wallet_url' method.
    """

    @abstractmethod
    def create_connect_wallet_url(self, universal_url: str, wallet_image: str) -> str:
        """
        Create a URL for connecting a wallet and generate a QR code.

        :param universal_url: Universal URL for connecting the wallet.
        :param wallet_image: Image URL associated with the wallet.
        :return: URL for generating the QR code.
        """
        raise NotImplementedError


class QRCodeProvider(QRCodeProviderBase):
    """
    Default implementation of the QRCodeProviderBase.

    Uses the 'qrcode.ness.su' service to create a QR code with specific parameters.
    """

    def create_connect_wallet_url(self, universal_url: str, wallet_image: str) -> str:
        """
        Create a URL for connecting a wallet and generate a QR code.

        :param universal_url: Universal URL for connecting the wallet.
        :param wallet_image: Image URL associated with the wallet.
        :return: URL for generating the QR code.
        """
        encoded_universal_url = base64.b64encode(universal_url.encode()).decode()
        encoded_wallet_image = base64.b64encode(wallet_image.encode()).decode()
        return (
            f"https://qrcode.ness.su/create?box_size=20&border=7&image_padding=20"
            f"&data={encoded_universal_url}"
            f"&image_url={encoded_wallet_image}"
        )
