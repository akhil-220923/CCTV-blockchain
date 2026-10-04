import json
import time
import copy
from typing import List, Dict, Any
from .crypto_utils import calculate_data_sha256, compute_merkle_root


class Block:
    """Represents a tamper-evident block in the Border Surveillance Blockchain."""

    def __init__(
        self,
        index: int,
        transactions: List[Dict[str, Any]],
        previous_hash: str,
        timestamp: float = None,
        validator_node: str = "BorderPolice-Node",
        nonce: int = 0,
        block_hash: str = None
    ):
        self.index = index
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.transactions = copy.deepcopy(transactions)
        self.previous_hash = previous_hash
        self.validator_node = validator_node
        self.nonce = nonce
        self.merkle_root = self.compute_merkle_root()
        self.hash = block_hash if block_hash is not None else self.calculate_hash()

    def compute_merkle_root(self) -> str:
        """Compute the Merkle root of all transactions in this block."""
        tx_hashes = [
            calculate_data_sha256(json.dumps(tx, sort_keys=True))
            for tx in self.transactions
        ]
        return compute_merkle_root(tx_hashes)

    def calculate_hash(self) -> str:
        """Calculate the SHA-256 hash of the block header."""
        block_header = {
            "index": self.index,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "merkle_root": self.merkle_root,
            "validator_node": self.validator_node,
            "nonce": self.nonce
        }
        return calculate_data_sha256(json.dumps(block_header, sort_keys=True))

    def verify_integrity(self) -> bool:
        """Verify that the block hash and Merkle root are cryptographically intact."""
        recomputed_merkle = self.compute_merkle_root()
        if recomputed_merkle != self.merkle_root:
            return False
        recomputed_hash = self.calculate_hash()
        return recomputed_hash == self.hash

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "merkle_root": self.merkle_root,
            "validator_node": self.validator_node,
            "nonce": self.nonce,
            "hash": self.hash,
            "transactions": self.transactions
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Block":
        block = cls(
            index=data["index"],
            transactions=data["transactions"],
            previous_hash=data["previous_hash"],
            timestamp=data["timestamp"],
            validator_node=data.get("validator_node", "Unknown-Node"),
            nonce=data.get("nonce", 0),
            block_hash=data["hash"]
        )
        block.merkle_root = data.get("merkle_root", block.compute_merkle_root())
        return block
