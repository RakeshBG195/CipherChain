"""
Ethereum ledger access through Web3.py.
Supports local Hardhat and signed Sepolia transactions.
"""
import json
import threading
import time
from typing import Optional

from backend.config import (
    DEPLOYMENT_FILE,
    HARDHAT_URL,
    DEPLOYER_PRIVATE_KEY,
)


class LedgerUnavailable(RuntimeError):
    pass


class Web3Ledger:
    def __init__(self, url=HARDHAT_URL, deployment_file=DEPLOYMENT_FILE):
        self.url = url
        self.deployment_file = deployment_file
        self.private_key = DEPLOYER_PRIVATE_KEY
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
                raise LedgerUnavailable(
                    f"contract deployment file missing: {self.deployment_file}"
                )

            try:
                dep = json.loads(self.deployment_file.read_text())
                w3 = Web3(
                    Web3.HTTPProvider(
                        self.url,
                        request_kwargs={"timeout": 15}
                    )
                )

                if not w3.is_connected():
                    raise LedgerUnavailable("cannot connect to blockchain RPC")

                if int(w3.eth.chain_id) != int(dep["chainId"]):
                    raise LedgerUnavailable("RPC network does not match deployed contract")

                addr = Web3.to_checksum_address(dep["address"])

                if len(w3.eth.get_code(addr)) == 0:
                    raise LedgerUnavailable("no contract code at deployed address")

                self.w3 = w3
                self.contract = w3.eth.contract(
                    address=addr,
                    abi=dep["abi"]
                )

            except LedgerUnavailable:
                raise
            except Exception as e:
                raise LedgerUnavailable(f"blockchain setup failed: {e}") from e

    def record(self, chain_key: int, hash_hex: str) -> dict:
        self._ensure()

        try:
            payload = bytes.fromhex(hash_hex.removeprefix("0x"))

            if len(payload) != 32:
                raise ValueError("message hash must be exactly 32 bytes")

            function = self.contract.functions.recordMessage(
                chain_key,
                payload
            )

            if self.private_key:
                account = self.w3.eth.account.from_key(self.private_key)
                tx = function.build_transaction({
                    "from": account.address,
                    "nonce": self.w3.eth.get_transaction_count(
                        account.address, "pending"
                    ),
                    "chainId": self.w3.eth.chain_id,
                    "gasPrice": self.w3.eth.gas_price,
                })

                signed = account.sign_transaction(tx)
                raw_tx = getattr(
                    signed,
                    "raw_transaction",
                    getattr(signed, "rawTransaction", None)
                )

                if raw_tx is None:
                    raise ValueError("could not obtain signed transaction bytes")

                tx_hash = self.w3.eth.send_raw_transaction(raw_tx)

            elif int(self.w3.eth.chain_id) == 31337:
                tx_hash = function.transact({
                    "from": self.w3.eth.accounts[0]
                })

            else:
                raise ValueError(
                    "DEPLOYER_PRIVATE_KEY is required for public networks"
                )

            receipt = self.w3.eth.wait_for_transaction_receipt(
                tx_hash, timeout=60
            )

            if receipt.status != 1:
                raise ValueError("blockchain transaction was reverted")

            block = self.w3.eth.get_block(receipt.blockNumber)

        except Exception as e:
            raise LedgerUnavailable(f"transaction failed: {e}") from e

        return {
            "tx_hash": tx_hash.hex(),
            "block_number": int(receipt.blockNumber),
            "timestamp": int(block.timestamp),
        }

    def get(self, chain_key: int) -> Optional[dict]:
        """Return the stored hash and timestamp, or None if not recorded."""
        self._ensure()

        try:
            h, ts, _rec, exists = (
                self.contract.functions.getRecord(chain_key).call()
            )
        except Exception as e:
            raise LedgerUnavailable(f"blockchain read failed: {e}") from e

        return {"hash": h.hex(), "timestamp": int(ts)} if exists else None

    def status(self) -> dict:
        try:
            self._ensure()
            return {
                "connected": True,
                "url": self.url,
                "contract_address": self.contract.address,
                "chain_id": int(self.w3.eth.chain_id),
                "block_number": int(self.w3.eth.block_number),
                "total_records": int(
                    self.contract.functions.totalRecords().call()
                ),
            }
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
