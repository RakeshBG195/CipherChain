"""
End-to-end encryption protocol (reference implementation, byte-compatible with frontend/src/lib/e2ee.js).

  * Identity keys : ECDH on NIST P-256. Public key is exchanged as 65-byte uncompressed point (base64).
  * Session key   : HKDF-SHA256( ECDH shared secret,
                                 salt = SHA256(sorted(pubA, pubB)),
                                 info = "secure-messaging-v1|conv:<conversation_id>" ) -> 32 bytes
  * Cipher        : AES-256-GCM, fresh random 96-bit nonce per message,
                    AAD = "<conversation_id>|<sender_id>"
  * Integrity hash: SHA-256 of "v1|<conv>|<sender>|<nonce_b64>|<ciphertext_b64>"  (this is what goes on-chain)

The SERVER only ever uses validate_public_key() and payload_hash(). It never sees private keys or plaintext.
"""
import base64
import hashlib
import os
from typing import Tuple

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

PROTOCOL = "secure-messaging-v1"
NONCE_BYTES = 12


def b64e(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")


def b64d(s: str) -> bytes:
    return base64.b64decode(s.encode("ascii"), validate=True)


def public_to_raw(pub: ec.EllipticCurvePublicKey) -> bytes:
    return pub.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)


def raw_to_public(raw: bytes) -> ec.EllipticCurvePublicKey:
    return ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), raw)


def generate_keypair() -> Tuple[ec.EllipticCurvePrivateKey, bytes]:
    priv = ec.generate_private_key(ec.SECP256R1())
    return priv, public_to_raw(priv.public_key())


def validate_public_key(b64: str) -> bytes:
    """Return raw bytes if b64 is a valid P-256 uncompressed point on the curve, else raise ValueError."""
    try:
        raw = b64d(b64)
        if len(raw) != 65 or raw[0] != 0x04:
            raise ValueError("public key must be a 65-byte uncompressed P-256 point")
        raw_to_public(raw)  # raises ValueError if the point is not on the curve
        return raw
    except Exception as exc:
        raise ValueError(f"invalid public key: {exc}") from exc


def derive_conversation_key(priv: ec.EllipticCurvePrivateKey, my_pub_raw: bytes,
                            peer_pub_raw: bytes, conversation_id: int) -> bytes:
    shared = priv.exchange(ec.ECDH(), raw_to_public(peer_pub_raw))
    salt = hashlib.sha256(b"".join(sorted([my_pub_raw, peer_pub_raw]))).digest()
    info = f"{PROTOCOL}|conv:{conversation_id}".encode()
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=salt, info=info).derive(shared)


def _aad(conversation_id: int, sender_id: int) -> bytes:
    return f"{conversation_id}|{sender_id}".encode()


def encrypt(key: bytes, plaintext: str, conversation_id: int, sender_id: int) -> Tuple[str, str]:
    nonce = os.urandom(NONCE_BYTES)
    ct = AESGCM(key).encrypt(nonce, plaintext.encode("utf-8"), _aad(conversation_id, sender_id))
    return b64e(nonce), b64e(ct)


def decrypt(key: bytes, nonce_b64: str, ciphertext_b64: str, conversation_id: int, sender_id: int) -> str:
    """Raises cryptography.exceptions.InvalidTag if key, AAD or ciphertext is wrong/modified."""
    pt = AESGCM(key).decrypt(b64d(nonce_b64), b64d(ciphertext_b64), _aad(conversation_id, sender_id))
    return pt.decode("utf-8")


def payload_hash(conversation_id: int, sender_id: int, nonce_b64: str, ciphertext_b64: str) -> str:
    data = f"v1|{conversation_id}|{sender_id}|{nonce_b64}|{ciphertext_b64}".encode("utf-8")
    return hashlib.sha256(data).hexdigest()
