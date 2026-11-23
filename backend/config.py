"""Central configuration. Everything can be overridden with environment variables."""
import os
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Load local blockchain settings from smart-contracts/.env
ENV_FILE = ROOT / "smart-contracts" / ".env"
if ENV_FILE.is_file():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value

DB_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{(ROOT / 'backend' / 'secure_messaging.db').as_posix()}"
)

if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DB_URL.startswith("postgresql://"):
    DB_URL = DB_URL.replace("postgresql://", "postgresql+psycopg://", 1)

MODEL_DIR = Path(os.getenv("MODEL_DIR", ROOT / "trained_models_real"))

_default_deployment = (
    "sepolia.json" if os.getenv("SEPOLIA_RPC_URL") else "localhost.json"
)

DEPLOYMENT_FILE = Path(os.getenv(
    "DEPLOYMENT_FILE",
    ROOT / "smart-contracts" / "deployments" / _default_deployment
))

HARDHAT_URL = os.getenv(
    "HARDHAT_URL",
    os.getenv("SEPOLIA_RPC_URL", "http://127.0.0.1:8545")
)

DEPLOYER_PRIVATE_KEY = os.getenv("DEPLOYER_PRIVATE_KEY", "")

ALLOW_DEV_TAMPER = os.getenv("ALLOW_DEV_TAMPER", "0") == "1"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "12"))
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://127.0.0.1:3000,http://localhost:3000"
).split(",")


def get_jwt_secret() -> str:
    env = os.getenv("JWT_SECRET")
    if env:
        return env
    f = ROOT / "backend" / ".jwt_secret"
    if not f.exists():
        f.write_text(secrets.token_hex(32))
    return f.read_text().strip()