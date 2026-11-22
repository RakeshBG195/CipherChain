"""
End-to-end test against a RUNNING stack (backend :8000, Hardhat node :8545 with the contract deployed, model trained).
Start the backend with ALLOW_DEV_TAMPER=1 so the tamper step can run.   Usage:  python -m scripts.e2e_test

Covers: register 2 users, login both, ECDH/HKDF session key, encrypted send, ciphertext-only storage check via API,
decrypt at receiver, on-chain verification, tamper detection, SAFE/SPAM/PHISHING classification, dashboard from API.
"""
import json, os, sys, time, urllib.error, urllib.request
from backend.crypto import e2ee

BASE = os.getenv("API_BASE", "http://127.0.0.1:8000/api")
results = []


def call(method, path, body=None, token=None):
    req = urllib.request.Request(BASE + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json", **({"Authorization": f"Bearer {token}"} if token else {})})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"null")


def check(name, cond, extra=""):
    results.append((name, bool(cond))); print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""))


def main():
    sfx = str(int(time.time()))[-6:]
    users = {}
    for n in ("alice", "bob"):
        priv, pub = e2ee.generate_keypair()
        s, r = call("POST", "/auth/register", {"username": f"{n}_{sfx}", "email": f"{n}{sfx}@example.com", "password": "S3cure-Pass!", "display_name": n.title(), "public_key": e2ee.b64e(pub)})
        check(f"register {n}", s == 201, r)
        s2, r2 = call("POST", "/auth/login", {"username": f"{n}_{sfx}", "password": "S3cure-Pass!"})
        check(f"login {n}", s2 == 200 and r2["token"], r2)
        users[n] = {"priv": priv, "pub": pub, "token": r2["token"], "id": r2["user"]["id"]}
    A, B = users["alice"], users["bob"]
    check("wrong password rejected", call("POST", "/auth/login", {"username": f"alice_{sfx}", "password": "nope"})[0] == 401)
    check("no token rejected", call("GET", "/users/me")[0] == 401)

    s, conv = call("POST", "/conversations", {"peer_id": B["id"]}, A["token"]); check("create conversation", s == 200, conv)
    cid = conv["id"]
    s, bpub = call("GET", "/conversations", token=A["token"]); peer_pub = e2ee.b64d(bpub[0]["peer"]["public_key"])
    ka = e2ee.derive_conversation_key(A["priv"], A["pub"], peer_pub, cid)
    kb = e2ee.derive_conversation_key(B["priv"], B["pub"], A["pub"], cid)
    check("ECDH+HKDF session keys match on both sides", ka == kb)

    plain = "hello bob, the secret meeting is at 5pm"
    nonce, ct = e2ee.encrypt(ka, plain, cid, A["id"])
    s, sent = call("POST", f"/conversations/{cid}/messages", {"nonce": nonce, "ciphertext": ct}, A["token"]); check("send encrypted message", s == 201, sent)
    mid = sent["id"]
    s, lst = call("GET", f"/conversations/{cid}/messages", token=B["token"])
    check("API returns ciphertext only (no plaintext field/content)", s == 200 and "hello bob" not in json.dumps(lst) and "plain" not in json.dumps(lst))
    check("receiver decrypts", e2ee.decrypt(kb, lst[0]["nonce"], lst[0]["ciphertext"], cid, A["id"]) == plain)
    check("server payload hash equals client-computed hash", lst[0]["payload_hash"] == e2ee.payload_hash(cid, A["id"], nonce, ct))

    s, st = call("GET", "/blockchain/status", token=A["token"])
    check("blockchain node + contract reachable", s == 200 and st.get("connected"), st)
    s, v = call("GET", f"/blockchain/verify/{mid}", token=B["token"])
    check("on-chain verification == VERIFIED", s == 200 and v["status"] == "VERIFIED", v)
    check("on-chain hash equals locally computed hash", v.get("onchain_hash") == e2ee.payload_hash(cid, A["id"], nonce, ct))

    s, t = call("POST", f"/blockchain/dev/tamper/{mid}", token=A["token"])
    if s == 403:
        print("SKIP tamper test (start backend with ALLOW_DEV_TAMPER=1)")
    else:
        s, v = call("GET", f"/blockchain/verify/{mid}", token=B["token"])
        check("tampered ciphertext detected as TAMPERED", v["status"] == "TAMPERED", v)

    for label, text in (("SAFE", "are we still meeting for lunch at noon tomorrow?"),
                        ("SPAM", "WINNER! You have won a free iPhone, text CLAIM to 85555 now to get your prize"),
                        ("PHISHING", "Security alert: your PayPal account is suspended, verify your password at http://secure-login.xyz/verify immediately")):
        s, r = call("POST", "/ai/analyze", {"text": text}, A["token"])
        check(f"classify {label} -> got {r.get('category') if s == 200 else s}", s == 200 and r["category"] == label, r)

    s, d = call("GET", "/dashboard/summary", token=A["token"])
    check("dashboard summary from real API", s == 200 and d["totals"]["total_messages"] >= 1 and d["totals"]["encrypted_messages"] >= 1, d)
    ok = sum(1 for _, c in results if c); print(f"\n{ok}/{len(results)} checks passed")
    sys.exit(0 if ok == len(results) else 1)


if __name__ == "__main__":
    main()
