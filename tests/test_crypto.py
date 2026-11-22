import unittest
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from backend.crypto import e2ee
from backend.blockchain.integrity import evaluate_integrity, VERIFIED, TAMPERED, NOT_RECORDED


class CryptoTests(unittest.TestCase):
    def setUp(self):
        self.a_priv, self.a_pub = e2ee.generate_keypair()
        self.b_priv, self.b_pub = e2ee.generate_keypair()
        self.ka = e2ee.derive_conversation_key(self.a_priv, self.a_pub, self.b_pub, 7)
        self.kb = e2ee.derive_conversation_key(self.b_priv, self.b_pub, self.a_pub, 7)

    def test_ecdh_both_sides_same_key_len32(self):
        self.assertEqual(self.ka, self.kb)
        self.assertEqual(len(self.ka), 32)

    def test_key_bound_to_conversation(self):
        other = e2ee.derive_conversation_key(self.a_priv, self.a_pub, self.b_pub, 8)
        self.assertNotEqual(self.ka, other)

    def test_roundtrip(self):
        n, c = e2ee.encrypt(self.ka, "hello \u2603 world", 7, 1)
        self.assertEqual(e2ee.decrypt(self.kb, n, c, 7, 1), "hello \u2603 world")

    def test_ciphertext_does_not_contain_plaintext(self):
        n, c = e2ee.encrypt(self.ka, "super secret text", 7, 1)
        self.assertNotIn(b"super secret", e2ee.b64d(c))

    def test_nonce_unique_and_96bit(self):
        nonces = {e2ee.encrypt(self.ka, "x", 7, 1)[0] for _ in range(500)}
        self.assertEqual(len(nonces), 500)
        self.assertEqual(len(e2ee.b64d(next(iter(nonces)))), 12)

    def test_tampered_ciphertext_rejected(self):
        n, c = e2ee.encrypt(self.ka, "msg", 7, 1)
        raw = bytearray(e2ee.b64d(c)); raw[0] ^= 1
        with self.assertRaises(InvalidTag):
            e2ee.decrypt(self.kb, n, e2ee.b64e(bytes(raw)), 7, 1)

    def test_wrong_key_and_wrong_aad_rejected(self):
        n, c = e2ee.encrypt(self.ka, "msg", 7, 1)
        c_priv, c_pub = e2ee.generate_keypair()
        kc = e2ee.derive_conversation_key(c_priv, c_pub, self.a_pub, 7)
        with self.assertRaises(InvalidTag):
            e2ee.decrypt(kc, n, c, 7, 1)
        with self.assertRaises(InvalidTag):
            e2ee.decrypt(self.kb, n, c, 7, 2)   # sender id is authenticated
        with self.assertRaises(InvalidTag):
            e2ee.decrypt(self.kb, n, c, 99, 1)  # conversation id is authenticated

    def test_hkdf_rfc5869_vector(self):  # RFC 5869 test case 1 (validates the HKDF primitive wiring)
        ikm = bytes.fromhex("0b" * 22)
        salt = bytes.fromhex("000102030405060708090a0b0c")
        info = bytes.fromhex("f0f1f2f3f4f5f6f7f8f9")
        okm = HKDF(algorithm=hashes.SHA256(), length=42, salt=salt, info=info).derive(ikm)
        self.assertEqual(okm.hex(), "3cb25f25faacd57a90434f64d0362f2a2d2d0a90cf1a5a4c5db02d56ecc4c5bf34007208d5b887185865")

    def test_public_key_validation(self):
        self.assertEqual(e2ee.validate_public_key(e2ee.b64e(self.a_pub)), self.a_pub)
        for bad in ["", "AAAA", e2ee.b64e(b"\x04" + b"\x01" * 64), e2ee.b64e(b"\x02" + b"\x00" * 32)]:
            with self.assertRaises(ValueError):
                e2ee.validate_public_key(bad)

    def test_payload_hash_changes_on_any_field(self):
        n, c = e2ee.encrypt(self.ka, "m", 7, 1)
        h = e2ee.payload_hash(7, 1, n, c)
        self.assertEqual(len(h), 64)
        self.assertNotEqual(h, e2ee.payload_hash(7, 1, n, c[:-4] + "AAAA"))
        self.assertNotEqual(h, e2ee.payload_hash(7, 2, n, c))
        self.assertNotEqual(h, e2ee.payload_hash(8, 1, n, c))

    def test_integrity_decision(self):
        n, c = e2ee.encrypt(self.ka, "m", 7, 1)
        onchain = e2ee.payload_hash(7, 1, n, c)
        self.assertEqual(evaluate_integrity(e2ee.payload_hash(7, 1, n, c), onchain), VERIFIED)
        self.assertEqual(evaluate_integrity(e2ee.payload_hash(7, 1, n, c[:-4] + "AAAA"), onchain), TAMPERED)
        self.assertEqual(evaluate_integrity(onchain, None), NOT_RECORDED)


if __name__ == "__main__":
    unittest.main()
