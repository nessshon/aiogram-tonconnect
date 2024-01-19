import base64

from .generator import generate_qrcode

__all__ = [
    "QRCode",
]


class QRCode:
    """
    Uses the 'qrcode.ness.su' or your own service to create a QR code with specific parameters.
    """

    @classmethod
    async def create_connect_wallet_image(
            cls,
            universal_url: str,
            wallet_image_url: str,
    ) -> bytes:
        """
        Create a QR code image for connecting a wallet.

        :param universal_url: Universal URL for connecting the wallet.
        :param wallet_image_url: Image URL associated with the wallet.
        :return: Bytes representing the QR code image.
        """
        return await generate_qrcode(
            universal_url,
            border=7,
            box_size=20,
            image_url=wallet_image_url,
            image_padding=20,
            image_round=50,
        )

    @classmethod
    def create_connect_wallet_url(
            cls,
            universal_url: str,
            qrcode_base_url: str,
            wallet_image_url: str,
    ) -> str:
        """
        Create a URL for connecting a wallet and generate a QR code.

        :param universal_url: Universal URL for connecting the wallet.
        :param qrcode_base_url: Base URL for generating the QR code.
        :param wallet_image_url: Image URL associated with the wallet.
        :return: URL for generating the QR code.
        """
        return (
            f"{qrcode_base_url}/create?"
            f"box_size=20&border=7&image_padding=20"
            f"&data={base64.b64encode(universal_url.encode()).decode()}"
            f"&image_url={base64.b64encode(wallet_image_url.encode()).decode()}"
        )
