"""
Message-integrity flow using InMemoryLedger - a TEST DOUBLE that mimics the Solidity contract semantics
(write-once records, getRecord). It exists ONLY in tests. It does NOT test Web3.py, Hardhat or the contract itself;
those are covered by smart-contracts/test/MessageIntegrity.test.js and scripts/e2e_test.py (need network-installed deps).
"""
import unittest
from backend.blockchain.integrity import TAMPERED, VERIFIED, NOT_RECORDED, evaluate_integrity
from backend.crypto import e2ee


class InMemoryLedger:
    def __init__(self): self.rec = {}
    def record(self, key, h):
        if key in self.rec: raise ValueError("already recorded")
        self.rec[key] = h
    def get(self, key): return self.rec.get(key)


class IntegrityFlow(unittest.TestCase):
    def test_send_store_verify_tamper(self):
        a_priv, a_pub = e2ee.generate_keypair(); b_priv, b_pub = e2ee.generate_keypair()
        ka = e2ee.derive_conversation_key(a_priv, a_pub, b_pub, 1)
        kb = e2ee.derive_conversation_key(b_priv, b_pub, a_pub, 1)
        nonce, ct = e2ee.encrypt(ka, "meet at 5", 1, 10)
        db_row = {"nonce": nonce, "ciphertext": ct}                     # what the server stores: no plaintext
        self.assertNotIn("meet", str(db_row))
        ledger = InMemoryLedger(); ledger.record(0xABC, e2ee.payload_hash(1, 10, nonce, ct))

        recomputed = e2ee.payload_hash(1, 10, db_row["nonce"], db_row["ciphertext"])
        self.assertEqual(evaluate_integrity(recomputed, ledger.get(0xABC)), VERIFIED)
        self.assertEqual(e2ee.decrypt(kb, db_row["nonce"], db_row["ciphertext"], 1, 10), "meet at 5")

        raw = bytearray(e2ee.b64d(db_row["ciphertext"])); raw[3] ^= 0x80        # attacker edits DB
        db_row["ciphertext"] = e2ee.b64e(bytes(raw))
        recomputed = e2ee.payload_hash(1, 10, db_row["nonce"], db_row["ciphertext"])
        self.assertEqual(evaluate_integrity(recomputed, ledger.get(0xABC)), TAMPERED)
        with self.assertRaises(Exception):                                       # and AES-GCM independently rejects it
            e2ee.decrypt(kb, db_row["nonce"], db_row["ciphertext"], 1, 10)
        self.assertEqual(evaluate_integrity(recomputed, ledger.get(0xDEF)), NOT_RECORDED)

    def test_chain_key_from_uid(self):
        from backend.blockchain.service import chain_key
        self.assertEqual(chain_key("ff"), 255)
        self.assertLess(chain_key("f" * 32), 2 ** 256)


if __name__ == "__main__":
    unittest.main()
