import time, unittest
import jwt
from backend.auth.security import create_token, decode_token, hash_password, verify_password
from backend.config import get_jwt_secret


class AuthSecurityTests(unittest.TestCase):
    def test_password_hash_verify(self):
        h = hash_password("correct horse battery")
        self.assertTrue(h.startswith("scrypt$"))
        self.assertTrue(verify_password("correct horse battery", h))
        self.assertFalse(verify_password("wrong", h))
        self.assertNotEqual(h, hash_password("correct horse battery"))   # per-user random salt
        self.assertNotIn("correct horse", h)

    def test_malformed_hash_is_rejected_not_crashing(self):
        self.assertFalse(verify_password("x", "garbage"))

    def test_jwt_roundtrip_and_tamper(self):
        t = create_token(42)
        self.assertEqual(decode_token(t)["sub"], "42")
        with self.assertRaises(jwt.PyJWTError):
            decode_token(t[:-3] + ("AAA" if not t.endswith("AAA") else "BBB"))
        with self.assertRaises(jwt.PyJWTError):
            decode_token(jwt.encode({"sub": "1", "exp": int(time.time()) + 60}, "other-secret", algorithm="HS256"))
        with self.assertRaises(jwt.PyJWTError):
            decode_token(jwt.encode({"sub": "1", "exp": int(time.time()) - 10}, get_jwt_secret(), algorithm="HS256"))


if __name__ == "__main__":
    unittest.main()
