# CipherChain — AI-Powered Secure Messaging (AES-256-GCM · ECDH/HKDF · Blockchain integrity · NLP spam/phishing detection)

Final-year engineering project. **Read the status table first — several components were written without being able to
install or run their dependencies and are marked UNTESTED.**

## Status (honest)

| Component | Status |
|---|---|
| Crypto (AES-256-GCM, ECDH P-256, HKDF-SHA256, nonces, tamper rejection, RFC 5869 vector) | **Tested** (11 unit tests pass) |
| Browser WebCrypto library (`frontend/src/lib/e2ee.js`) ↔ Python reference | **Tested** under Node 22: JS→Python and Python→JS decrypt, identical on-chain hash |
| Password hashing (scrypt) + JWT | **Tested** (3 unit tests) |
| NLP pipeline (preprocess, TF-IDF, Logistic Regression, split, metrics, save/load, predictor, loaders) | **Tested** (8 unit tests, incl. corrupt-model handling) — but only on **SYNTHETIC** data, see below |
| Integrity decision logic VERIFIED / TAMPERED / NOT_RECORDED | **Tested** with an in-memory *test double* (tests only) |
| FastAPI app, SQLAlchemy models, WebSockets, all API routes | **Written, compiles, UNTESTED** (fastapi/sqlalchemy/uvicorn not installable offline) |
| Web3.py ledger service | **Written, UNTESTED** (web3 not installed, no node) |
| Solidity contract, Hardhat config/deploy/tests | **Written, UNTESTED** (cannot compile or run offline) |
| React frontend (8 pages) | **Written; all JS/JSX parse (esbuild); NOT built, NOT rendered, NOT browser-tested** |
| `scripts/e2e_test.py` (full workflow against a running stack) | **Written, UNTESTED** — this is what you run to validate everything |

Expect some integration bugs on first run of the untested parts; the e2e script and Hardhat tests are there to find them.

## Architecture & security model
* **Keys**: each browser generates a non-extractable ECDH P-256 key pair (IndexedDB). Only the public key goes to the server.
* **Session key**: `HKDF-SHA256(ECDH secret, salt = SHA256(sorted pubkeys), info = "secure-messaging-v1|conv:<id>")` → 32 bytes.
* **Message**: AES-256-GCM, random 96-bit nonce, AAD = `conversation_id|sender_id`. Encryption/decryption happen **only in the browser**.
* **Server DB** stores `nonce`, `ciphertext`, `payload_hash` — there is no plaintext column.
* **Blockchain**: `SHA-256("v1|conv|sender|nonce|ciphertext")` is written to `MessageIntegrity.sol` (write-once per message id). Verification recomputes the hash from the stored payload and compares with the contract; the browser also recomputes it locally. Result: `VERIFIED` / `TAMPERED` / `NOT_RECORDED` / `UNAVAILABLE`. If the node is down the UI says so — nothing is simulated.
* **AI**: the *receiving* client decrypts, then sends the plaintext to `/api/ai/analyze` **in memory**; only category/risk/confidence are stored. (Trade-off: the server momentarily sees plaintext of messages that are scanned. A fully private design would run the model in the browser — future work.)

## Install & run (Windows PowerShell)
Prerequisites: Python 3.10+, Node.js 18+ (20 LTS recommended), internet for first install (npm/pip/solc download).

```powershell
cd secure-messaging

# 1) Python environment
python -m venv .venv
# if script execution is blocked:  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2) Train the model  (see "Datasets" — real data strongly recommended)
python -m scripts.train_model --synthetic            # DEMO ONLY: synthetic data, metrics meaningless
# real:  python -m scripts.train_model --sms datasets\SMSSpamCollection --phishing datasets\phishing_email.csv

# 3) Blockchain — terminal A (leave running)
cd smart-contracts
npm install
npx hardhat test                                      # run contract tests first
npm run node                                          # http://127.0.0.1:8545

# 4) Deploy contract — terminal B (writes smart-contracts\deployments\localhost.json)
cd smart-contracts
npm run deploy

# 5) Backend — terminal C  (project root, venv active)
$env:ALLOW_DEV_TAMPER = "1"                           # optional: enables the tamper demo endpoint
uvicorn backend.main:app --host 127.0.0.1 --port 8000   # http://127.0.0.1:8000/docs

# 6) Frontend — terminal D
cd frontend
npm install
npm run dev                                           # http://127.0.0.1:3000
```
If you restart the Hardhat node its chain is wiped: run `npm run deploy` again (old messages then show NOT_RECORDED).

## Demo script
1. Register two users in two different browsers (or one normal + one private window) → each generates keys.
2. User A searches for B, sends messages; watch the *Live encryption trace* and the VERIFIED badge.
3. Send a spam/phishing-like text; B's client flags it (red banner, collapsed text).
4. Tamper demo: with `ALLOW_DEV_TAMPER=1`, `POST /api/blockchain/dev/tamper/{message_id}` (use `/docs`, Authorize with a token) → reopen the chat: **TAMPERED**, decryption fails (GCM tag).

## Datasets & model — read this
Nothing is downloaded automatically. See `datasets/README.md`. Without real data, `--synthetic` produces **template-generated**
messages; the resulting ~100 % metrics are an artefact of templating and **say nothing about real-world accuracy**
(`metrics.json` carries `synthetic_data: true` and the UI shows a warning banner). For the report, train on the UCI SMS Spam
Collection (SAFE/SPAM) **plus** a real labeled phishing corpus, and discuss the domain gap (SMS/e-mail ≠ chat) and the single hold-out split.
A DEMO model trained on synthetic data is bundled (see `trained_models/MODEL_INFO.md`; saved with one scikit-learn version — if it fails to load, the backend says so and you simply retrain, step 2). Artifacts: `trained_models/spam_phishing_model.joblib`, `trained_models/tfidf_vectorizer.joblib`, `trained_models/metrics.json`.
Retrain any time with `python -m scripts.train_model ...`; restart the backend to reload.

## Tests
```powershell
python -m unittest tests.test_crypto tests.test_ai tests.test_auth_security tests.test_integrity_flow tests.test_interop -v
cd smart-contracts; npx hardhat test                   # contract tests
python -m scripts.e2e_test                             # full workflow vs running stack (backend + hardhat + model)
```

## API
`POST /api/auth/register|login` · `GET|PUT /api/users/me` · `PUT /api/users/me/public-key` · `GET /api/users?q=` ·
`POST|GET /api/conversations` · `POST|GET /api/conversations/{id}/messages` · `POST /api/conversations/{id}/read` ·
`POST /api/ai/analyze` · `GET /api/ai/status|metrics|threats` · `GET /api/blockchain/status|records|verify/{id}` ·
`POST /api/blockchain/retry` · `POST /api/blockchain/dev/tamper/{id}` (demo, env-gated) · `GET /api/dashboard/summary` ·
`WS /ws?token=<jwt>` (events: `message.new`, `message.status`, `message.read`, `presence`) · `GET /api/health`

## Incomplete / not implemented
* Typing indicators, group chats, key backup, multi-device, forward secrecy, in-browser ML inference, password reset, rate limiting, HTTPS/WSS deployment config.
* Frontend visual polish and responsive layout are unverified until you run it.

## Known limitations
No key backup/multi-device; private key loss = unreadable history. No forward secrecy (static identity keys). The API server
reports on-chain data to the browser (a malicious server could lie; a hardened client would query the node itself). Sync
SQLAlchemy calls inside async routes (fine for a demo, not for scale). Hardhat account #0 signs all transactions.

## Note on pre-existing files
The workspace already contained an earlier, separate implementation (`backend/app/`, some `frontend/src` files, `scripts/demo_crypto.py`,
`scripts/generate_synthetic_dataset.py`, `datasets/synthetic_demo.csv`, `trained_models/model.joblib|vectorizer.joblib`, and
`tests/test_api_flow.py`, `test_blockchain_logic.py`, `test_chain_hardhat.py`, `conftest_env.py`). They are **not** used by this
codebase and their tests import a different package layout, so run the test commands above rather than `unittest discover`.
