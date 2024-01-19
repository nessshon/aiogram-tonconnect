from io import BytesIO
from typing import Union

import aiohttp
from PIL import Image, ImageDraw
from cachetools import TTLCache
from qrcode_styled import QRCodeStyled

# Initialize cache for storing generated QR codes for 24 hours
cache = TTLCache(maxsize=10_000, ttl=86000)


async def download_image_from_url(image_url: str) -> BytesIO:
    """
    Downloads an image from a given URL.

    :param image_url: URL of the image
    :return: BytesIO object containing the image data
    :raises ValueError: If image download fails, content type is not an image, or image format is unsupported
    """
    # Check if the image is already in the cache
    image_cache = cache.get(image_url)
    if image_cache:
        return BytesIO(image_cache)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                response.raise_for_status()

                # Check if the content type is an image
                content_type = response.headers.get('Content-Type', '').lower()

                # Check if the image format is supported (jpeg or png)
                if not content_type.startswith('image/jpeg') and not content_type.startswith('image/png'):
                    raise ValueError(f"Unsupported image format: {content_type}")

                image_data = await response.read()
                cache.setdefault(image_url, image_data)
                return BytesIO(image_data)

    except Exception as e:
        raise ValueError(f"Failed to download image from URL: {image_url}. Error: {e}")


async def generate_qrcode(
        data: str,
        border: int,
        box_size: int,
        image_url: Union[str, None] = None,
        image_padding: int = 10,
        image_round: int = 50,
) -> bytes:
    """
    Generates a styled QR code from data with an optional image inclusion.

    :param data: Data to be encoded in the QR code
    :param border: Border size of the QR code
    :param box_size: Size of each box in the QR code
    :param image_url: URL of the image to be included in the QR code (optional)
    :param image_padding: Padding around the optional image in the QR code (optional)
    :param image_round: Radius for rounding corners of the optional image in the QR code (optional)
    :return: BytesIO object containing the generated QR code image
    :raises ValueError: If there is an error in generating the QR code
    """
    try:
        image_id = f"{data}_{border}_{box_size}_{image_url}_{image_padding}_{image_round}"
        # Check if the image URL is in the cache
        if image_id in cache:
            return cache.get(image_id)

        # Download and process the optional image
        logo_image_stream = await download_image_from_url(image_url) if image_url else None
        padded_image = process_optional_image(logo_image_stream, image_padding, image_round)

        # Generate the QR code using qrcode_styled library
        qr = QRCodeStyled(border=border, box_size=box_size)
        qrcode_image = await qr.get_buffer_async(data=data, image=padded_image)
        qrcode_image_data = qrcode_image.getvalue()

        # Cache the generated QR code
        cache.setdefault(image_id, qrcode_image_data)

        return qrcode_image_data

    except (Exception,):
        raise


def process_optional_image(
        image_stream: BytesIO,
        image_padding: int = 10,
        image_round: int = 50,
) -> Image:
    """
    Processes an optional image to be included in the QR code.

    :param image_stream: BytesIO object containing the image data
    :param image_padding: Padding around the optional image in the QR code (optional)
    :param image_round: Radius for rounding corners of the optional image in the QR code (optional)
    :return: Processed Image object
    """
    if image_stream:
        logo_image = Image.open(image_stream).convert("RGBA")

        # If the image has an alpha channel (transparency), replace transparent areas with white
        if logo_image.mode == 'RGBA':
            alpha = logo_image.split()[3]
            white_background = Image.new("RGBA", logo_image.size, (255, 255, 255, 255))
            white_background.paste(logo_image, (0, 0), alpha)
            logo_image = white_background

        # Create a rounded rectangle mask for the logo image
        mask = Image.new("L", logo_image.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, logo_image.width, logo_image.height), image_round, fill=255)

        # Apply the mask to the logo image
        logo_image.putalpha(mask)
        logo_image = Image.alpha_composite(Image.new("RGBA", logo_image.size, (255, 255, 255, 255)), logo_image)

        # Add padding to the logo image
        padded_size = (logo_image.width + 2 * image_padding, logo_image.height + 2 * image_padding)
        padded_image = Image.new("RGBA", padded_size, (255, 255, 255, 255))
        padded_image.paste(logo_image, (image_padding, image_padding))

        return padded_image

    return None
