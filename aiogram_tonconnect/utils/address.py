import base64
import struct

from pydantic import BaseModel

__all__ = [
    "Address",
    "raw_to_userfriendly",
]


class Address(BaseModel):
    """
    Represents a TON address with methods for user-friendly display and conversion.

    :Attributes:
    - hex_address (str): Raw TON address in the format "workchain_id:key".

    :Methods:
    - __str__(): Returns a user-friendly address with urlSafe=true and bounceable=false format.
    - to_raw(): Returns the raw TON address.
    - to_userfriendly(test_only: bool = False): Returns a user-friendly address with optional testnet support.
    """
    hex_address: str

    def __str__(self) -> str:
        """
        Returns a user-friendly address with urlSafe=true and bounceable=false format.
        """
        return raw_to_userfriendly(self.hex_address)

    def to_raw(self) -> str:
        """
        Returns the raw TON address.
        """
        return self.hex_address

    def to_userfriendly(self, test_only: bool = False) -> str:
        """
        Returns a user-friendly address with optional testnet support.
        """
        return raw_to_userfriendly(self.hex_address, test_only)


def _calculate_crc_xmodem(payload: bytes) -> int:
    crc = 0
    poly = 0x1021  # CRC-16 Xmodem polynomial

    for byte in payload:
        crc ^= (byte << 8)  # XOR with the next byte

        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ poly
            else:
                crc <<= 1

    return crc & 0xFFFF  # Keep only the lower 16 bits


def raw_to_userfriendly(address: str, test_only: bool = False) -> str:
    """
    Converts a raw address string to a user-friendly format.

    :param address: The raw address string in the format "workchain_id:key".
    :param test_only: The flag indicating if the address is bounceable. Defaults to False.
    :return: The user-friendly address string, encoded in base64 and URL-safe.
    """
    tag = 0x51
    if test_only:
        tag ^= 0x80
    workchain_id, key = address.split(':')
    workchain_id = int(workchain_id)
    key = bytearray.fromhex(key)

    short_ints = [j * 256 + i for i, j in zip(*[iter(key)] * 2)]
    payload = struct.pack(f'Bb{"H" * 16}', tag, workchain_id, *short_ints)
    crc = _calculate_crc_xmodem(payload)
    encoded_key = payload + struct.pack('>H', crc)

    return base64.urlsafe_b64encode(encoded_key).decode("utf-8")
