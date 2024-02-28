import base64
from abc import ABCMeta, abstractmethod

from .generator import generate_qrcode

__all__ = [
    "QRImageProviderBase",
    "QRUrlProviderBase",

    "QRImageProvider",
    "QRUrlProvider",
]


class QRImageProviderBase(metaclass=ABCMeta):

    @classmethod
    @abstractmethod
    async def create_connect_wallet_image(cls, universal_url: str, *args, **kwargs) -> bytes:
        """
        Create a QR code image for connecting a wallet.

        :param universal_url: Universal URL for connecting the wallet.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: Bytes representing the QR code image.
        """
        raise NotImplementedError(
            "Implement the method to generate the QR code image "
            "in bytes from the universal_url data."
        )


class QRUrlProviderBase(metaclass=ABCMeta):

    @classmethod
    @abstractmethod
    async def create_connect_wallet_image_url(cls, universal_url: str, *args, **kwargs) -> str:
        """
        Create a URL for connecting a wallet and generate a QR code.

        :param universal_url: Universal URL for connecting the wallet.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: URL for generating the QR code.
        """
        raise NotImplementedError(
            "Implement the method to generate the QR code and retry the URL string "
            "using your API from the universal_url data."
        )


class QRImageProvider(QRImageProviderBase):

    @classmethod
    async def create_connect_wallet_image(cls, universal_url: str, *args, **kwargs) -> bytes:
        return await generate_qrcode(
            universal_url,
            border=7,
            box_size=20,
            image_url=args[0],
            image_padding=20,
            image_round=50,
        )


class QRUrlProvider(QRUrlProviderBase):

    @classmethod
    async def create_connect_wallet_image_url(cls, universal_url: str, *args, **kwargs) -> str:
        return (
            f"https://qrcode.ness.su/create?"
            f"box_size=20&border=7&image_padding=20"
            f"&data={base64.b64encode(universal_url.encode()).decode()}"
            f"&image_url={base64.b64encode(args[0].encode()).decode()}"
        )
