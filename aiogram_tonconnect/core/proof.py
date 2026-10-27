import logging
import typing as t
from dataclasses import dataclass

from nacl.exceptions import BadSignatureError
from ton_connect import VerifySignData, VerifyTonProof, create_ton_proof_payload, verify_ton_proof_payload
from ton_connect.models import Account, SignDataPayloadDto, SignDataResult, Wallet
from ton_core import Address, PublicKey

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TonProof:
    """Signature checks: ``ton_proof`` on every connect and the signature of every ``sign_data``."""

    domain: str
    """The host of the manifest ``url`` field: wallets sign for it."""
    secret: str
    """Key of the ``ton_proof`` challenges; it must outlive restarts, or a challenge issued before one fails."""
    ttl: int = 300
    """Maximum age of a signature in seconds; also the lifetime of a challenge and the wait for a connection."""
    get_wallet_public_key: t.Callable[[Address], t.Awaitable[PublicKey | None]] | None = None
    """Current key of key-rotating wallets such as the Telegram one; without it their initial key is trusted."""

    def challenge(self) -> str:
        """Return a new ``ton_proof`` payload for the wallet to sign."""
        return create_ton_proof_payload(self.secret, self.ttl)

    async def check_connect(self, wallet: Wallet) -> Exception | None:
        """Check the ``ton_proof`` of a connected wallet; return why it fails, or ``None``."""
        dto = wallet.ton_proof_dto
        if dto is None or dto.proof is None:
            return BadSignatureError("The wallet sent no ton_proof")
        try:
            verify_ton_proof_payload(self.secret, dto.proof.payload)
        except BadSignatureError as error:
            return error
        return await self._verify(VerifyTonProof(dto), wallet.account.address)

    async def check_sign_data(self, account: Account, result: SignDataResult) -> Exception | None:
        """Check the signature of a ``sign_data`` result; return why it fails, or ``None``."""
        dto = SignDataPayloadDto(
            address=account.address,
            network=account.network,
            public_key=account.public_key,
            wallet_state_init=account.state_init,
            signature=result.signature,
            timestamp=result.timestamp,
            domain=result.domain,
            payload=result.payload,
        )
        return await self._verify(VerifySignData(dto), account.address)

    async def _verify(self, verifier: VerifyTonProof | VerifySignData, address: Address) -> Exception | None:
        try:
            valid = await verifier.verify(
                allowed_domains=[self.domain],
                valid_auth_time=self.ttl,
                get_wallet_public_key=self.get_wallet_public_key,
            )
        except BadSignatureError as error:
            # A wrong, expired or foreign signature is the wallet's: the operation fails, nothing to tell the bot owner
            return error
        except Exception as error:
            # A failed get_wallet_public_key of the bot leaves the key unknown, and an unchecked signature is not trusted
            logger.warning("Signature of %s could not be checked: %s", address.to_str(), error, exc_info=error)
            return error
        return None if valid else BadSignatureError("The signature is not valid")
