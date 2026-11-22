"""
Real Ethereum ledger access through Web3.py against the local Hardhat node.
If the node or the deployed contract is unreachable we raise LedgerUnavailable - we NEVER fake a verification.
"""
import json
import threading
import time
from typing import Optional

from backend.config import DEPLOYMENT_FILE, HARDHAT_URL


class LedgerUnavailable(RuntimeError):
    pass


class Web3Ledger:
    def __init__(self, url: str = HARDHAT_URL, deployment_file=DEPLOYMENT_FILE):
        self.url, self.deployment_file = url, deployment_file
        self.w3 = None
        self.contract = None
        self._last_try = 0.0
        self._lock = threading.Lock()

    def _ensure(self):
        with self._lock:
            if self.contract is not None and self.w3.is_connected():
                return
            if time.time() - self._last_try < 2:
                raise LedgerUnavailable("ledger not reachable (retrying shortly)")
            self._last_try = time.time()
            try:
                from web3 import Web3
            except ImportError as e:
                raise LedgerUnavailable("web3 package not installed") from e
            if not self.deployment_file.exists():
                raise LedgerUnavailable(f"contract not deployed: {self.deployment_file} missing (run the Hardhat deploy script)")
            dep = json.loads(self.deployment_file.read_text())
            w3 = Web3(Web3.HTTPProvider(self.url, request_kwargs={"timeout": 5}))
            if not w3.is_connected():
                raise LedgerUnavailable(f"cannot connect to blockchain node at {self.url}")
            addr = Web3.to_checksum_address(dep["address"])
            if len(w3.eth.get_code(addr)) == 0:
                raise LedgerUnavailable("no contract code at the deployed address (node restarted? redeploy the contract)")
            self.w3, self.contract = w3, w3.eth.contract(address=addr, abi=dep["abi"])

    def record(self, chain_key: int, hash_hex: str) -> dict:
        self._ensure()
        try:
            tx = self.contract.functions.recordMessage(chain_key, bytes.fromhex(hash_hex)).transact({"from": self.w3.eth.accounts[0]})
            rcpt = self.w3.eth.wait_for_transaction_receipt(tx, timeout=20)
            block = self.w3.eth.get_block(rcpt.blockNumber)
        except Exception as e:
            raise LedgerUnavailable(f"transaction failed: {e}") from e
        return {"tx_hash": tx.hex() if tx.hex().startswith("0x") else "0x" + tx.hex(),
                "block_number": int(rcpt.blockNumber), "timestamp": int(block.timestamp)}

    def get(self, chain_key: int) -> Optional[dict]:
        """Return {'hash': hex, 'timestamp': int} or None if the id was never recorded."""
        self._ensure()
        try:
            h, ts, _rec, exists = self.contract.functions.getRecord(chain_key).call()
        except Exception as e:
            raise LedgerUnavailable(f"call failed: {e}") from e
        return {"hash": h.hex(), "timestamp": int(ts)} if exists else None

    def status(self) -> dict:
        try:
            self._ensure()
            return {"connected": True, "url": self.url, "contract_address": self.contract.address,
                    "chain_id": int(self.w3.eth.chain_id), "block_number": int(self.w3.eth.block_number),
                    "total_records": int(self.contract.functions.totalRecords().call())}
        except LedgerUnavailable as e:
            return {"connected": False, "url": self.url, "error": str(e)}


_ledger = None


def get_ledger():
    global _ledger
    if _ledger is None:
        _ledger = Web3Ledger()
    return _ledger


def chain_key(uid_hex: str) -> int:
    return int(uid_hex, 16)
