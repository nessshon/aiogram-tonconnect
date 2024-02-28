import hashlib
from datetime import datetime
from nacl.utils import random
from nacl.signing import VerifyKey
from nacl.encoding import HexEncoder

from pytonconnect.logger import _LOGGER  # noqa

from aiogram_tonconnect.tonconnect.models import InfoWallet


def generate_payload(ttl: int = 600) -> str:
    payload = bytearray(random(8))

    ts = int(datetime.now().timestamp()) + ttl
    payload.extend(ts.to_bytes(8, 'big'))

    return payload.hex()


def check_payload(payload: str, info_wallet: InfoWallet) -> bool:
    if len(payload) < 32:
        return False
    if not check_proof(payload, info_wallet):
        return False
    ts = int(payload[16:32], 16)
    if datetime.now().timestamp() > ts:
        return False
    return True


def check_proof(src_payload: str, info_wallet: InfoWallet) -> bool:
    if not info_wallet.ton_proof:
        return False

    wc, whash = info_wallet.account.address.hex_address.split(':', maxsplit=2)

    message = bytearray('ton-proof-item-v2/'.encode())
    message.extend(int(wc, 10).to_bytes(4, 'little'))
    message.extend(bytes.fromhex(whash))
    message.extend(info_wallet.ton_proof.domain_len.to_bytes(4, 'little'))
    message.extend(info_wallet.ton_proof.domain_val.encode())
    message.extend(info_wallet.ton_proof.timestamp.to_bytes(8, 'little'))
    payload_to_use = src_payload.encode() if src_payload is not None else info_wallet.ton_proof.payload.encode()
    message.extend(payload_to_use)

    signature_message = bytearray.fromhex('ffff') + 'ton-connect'.encode() + hashlib.sha256(message).digest()

    try:
        verify_key = VerifyKey(info_wallet.account.public_key, HexEncoder)  # type: ignore
        verify_key.verify(hashlib.sha256(signature_message).digest(), bytes.fromhex(info_wallet.ton_proof.signature))
        return True
    except Exception as e:
        _LOGGER.error(f"Error verifying signature: {e}")

    return False
