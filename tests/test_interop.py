"""Cross-language check: the browser WebCrypto code (run under Node) and the Python reference must interoperate."""
import base64, json, shutil, subprocess, unittest
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import ec
from backend.crypto import e2ee

ROOT = Path(__file__).resolve().parent.parent
HELPER = ROOT / "tests" / "js" / "interop.mjs"


def run(mode, payload=None):
    r = subprocess.run(["node", str(HELPER), mode], input=json.dumps(payload or {}), capture_output=True, text=True, cwd=ROOT, timeout=60)
    if r.returncode != 0:
        raise RuntimeError(r.stderr)
    return json.loads(r.stdout)


def priv_from_jwk(jwk):
    pad = lambda s: s + "=" * (-len(s) % 4)
    return ec.derive_private_key(int.from_bytes(base64.urlsafe_b64decode(pad(jwk["d"])), "big"), ec.SECP256R1())


@unittest.skipUnless(shutil.which("node"), "node not installed")
class Interop(unittest.TestCase):
    def test_js_encrypts_python_decrypts_and_back(self):
        g = run("gen")
        pb = priv_from_jwk(g["B"]["jwk"])
        key_b = e2ee.derive_conversation_key(pb, e2ee.b64d(g["B"]["pub"]), e2ee.b64d(g["A"]["pub"]), 5)
        self.assertEqual(e2ee.decrypt(key_b, g["nonce"], g["ciphertext"], 5, 1), "hello from JS \u2603")   # JS -> Python
        self.assertEqual(e2ee.payload_hash(5, 1, g["nonce"], g["ciphertext"]), g["hash"])                   # identical hash
        pa = priv_from_jwk(g["A"]["jwk"])
        key_a = e2ee.derive_conversation_key(pa, e2ee.b64d(g["A"]["pub"]), e2ee.b64d(g["B"]["pub"]), 5)
        n, c = e2ee.encrypt(key_a, "hello from Python \u2603", 5, 1)
        out = run("dec", {"privJwk": g["B"]["jwk"], "myPub": g["B"]["pub"], "peerPub": g["A"]["pub"], "nonce": n, "ciphertext": c})
        self.assertEqual(out["text"], "hello from Python \u2603")                                           # Python -> JS
        self.assertEqual(out["hash"], e2ee.payload_hash(5, 1, n, c))


if __name__ == "__main__":
    unittest.main()
