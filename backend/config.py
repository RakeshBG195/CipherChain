"""Central configuration. Everything can be overridden with environment variables."""
import os
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_URL = os.getenv("DATABASE_URL", f"sqlite:///{(ROOT / 'backend' / 'secure_messaging.db').as_posix()}")
MODEL_DIR = Path(os.getenv("MODEL_DIR", ROOT / "trained_models_real"))
DEPLOYMENT_FILE = Path(os.getenv("DEPLOYMENT_FILE", ROOT / "smart-contracts" / "deployments" / "localhost.json"))
HARDHAT_URL = os.getenv("HARDHAT_URL", "http://127.0.0.1:8545")
# Demo-only endpoint that corrupts a stored ciphertext so TAMPERED detection can be shown. Off by default.
ALLOW_DEV_TAMPER = os.getenv("ALLOW_DEV_TAMPER", "0") == "1"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "12"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://127.0.0.1:3000,http://localhost:3000").split(",")


def get_jwt_secret() -> str:
    env = os.getenv("JWT_SECRET")
    if env:
        return env
    f = ROOT / "backend" / ".jwt_secret"
    if not f.exists():
        f.write_text(secrets.token_hex(32))
    return f.read_text().strip()
