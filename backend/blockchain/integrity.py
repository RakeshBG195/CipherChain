"""Pure integrity decision logic (no network). Used by the API and by unit tests."""
from typing import Optional

VERIFIED = "VERIFIED"
TAMPERED = "TAMPERED"
NOT_RECORDED = "NOT_RECORDED"
UNAVAILABLE = "UNAVAILABLE"


def evaluate_integrity(recomputed_hash: str, onchain_hash: Optional[str]) -> str:
    """Compare the hash recomputed from the stored encrypted payload against the on-chain hash."""
    if onchain_hash is None:
        return NOT_RECORDED
    return VERIFIED if recomputed_hash.lower() == onchain_hash.lower() else TAMPERED
