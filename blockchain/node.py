import time
import copy
from typing import Dict, List, Any, Optional
from .ledger import BlockchainLedger


class BlockchainNode:
    """
    Represents one of the 3 key stakeholder nodes:
    - Border Police Node (BSF / Tactical Field Operations)
    - State Police Node (Regional Law Enforcement & Inter-Agency Coordination)
    - Judiciary Node (Legal Evidence Scrutiny & Court of Law)
    """

    def __init__(self, node_id: str, organization: str, port: int, role: str, storage_dir: str = "blockchain_data"):
        self.node_id = node_id
        self.organization = organization
        self.port = port
        self.role = role
        self.ledger = BlockchainLedger(node_id=node_id, storage_dir=storage_dir)
        self.peers: Dict[str, "BlockchainNode"] = {}

    def connect_peer(self, peer_node: "BlockchainNode"):
        """Connect to a peer node in the 3-node network."""
        if peer_node.node_id != self.node_id:
            self.peers[peer_node.node_id] = peer_node

    def broadcast_transaction(self, tx_method_name: str, *args, **kwargs) -> Dict[str, Any]:
        """Execute a state-changing transaction locally and replicate exact block and audit entries across all 3 nodes."""
        method = getattr(self.ledger, tx_method_name)
        result = method(*args, **kwargs)

        # Synchronize exact mined block and audit entry across peer nodes (Consensus Replication)
        latest_block = self.ledger.chain[-1]
        latest_audit = self.ledger.audit_logs[-1] if self.ledger.audit_logs else None

        for peer_id, peer in self.peers.items():
            peer.ledger.receive_block(latest_block)
            if latest_audit:
                if not any(a.get("audit_id") == latest_audit["audit_id"] for a in peer.ledger.audit_logs):
                    peer.ledger.audit_logs.append(copy.deepcopy(latest_audit))
                    peer.ledger.save_to_disk()

        return result

    def sync_from_peers(self) -> Dict[str, Any]:
        """Check peer chains and verify that consensus is maintained across all 3 nodes."""
        status = {
            "local_node": self.node_id,
            "peers_checked": len(self.peers),
            "consensus_healthy": True,
            "tamper_detected": False,
            "details": []
        }

        for peer_id, peer in self.peers.items():
            remote_chain_dicts = [b.to_dict() for b in peer.ledger.chain]
            remote_audit_logs = [dict(a) for a in peer.ledger.audit_logs]
            remote_intrusions = {k: dict(v) for k, v in peer.ledger.intrusions.items()}
            tamper_check = self.ledger.detect_cross_node_tampering(
                remote_chain_dicts,
                peer_id,
                remote_audit_logs=remote_audit_logs,
                remote_intrusions=remote_intrusions
            )

            if tamper_check["tamper_detected"]:
                status["consensus_healthy"] = False
                status["tamper_detected"] = True
                status["details"].append({
                    "peer_id": peer_id,
                    "alerts": tamper_check["alerts"]
                })

        return status

    def audit_access_attempt(self, accessor_identity: str, action: str, target_id: str) -> Dict[str, Any]:
        """
        Log access to audit logs or evidence and notify peer nodes.
        'Suppose if someone accessed the audit log the rest of the nodes should know that they accessed and modified.'
        """
        ts = time.time()
        aid = f"AUDIT-{int(ts*1000)}-{len(self.ledger.audit_logs)}"
        entry = self.ledger.log_audit_access(
            accessor_node=self.node_id,
            accessor_identity=accessor_identity,
            action=action,
            target_id=target_id,
            status="LOGGED_AND_BROADCAST",
            details=f"{accessor_identity} accessed {target_id} on {self.node_id}",
            timestamp=ts,
            audit_id=aid
        )

        # Broadcast access notification to all other nodes so they know someone accessed it
        for peer_id, peer in self.peers.items():
            notice_id = f"NOTICE-{int(ts*1000)}-{peer_id[:4]}-{len(peer.ledger.audit_logs)}"
            peer.ledger.log_audit_access(
                accessor_node=self.node_id,
                accessor_identity=accessor_identity,
                action=f"REMOTE_NOTICE_{action}",
                target_id=target_id,
                status="PEER_NOTIFIED",
                details=f"INTER-AGENCY NOTICE: {accessor_identity} accessed {target_id} on {self.node_id}. Logged across consensus.",
                timestamp=ts,
                audit_id=notice_id
            )

        return entry

    def to_summary(self) -> Dict[str, Any]:
        valid, issues = self.ledger.verify_ledger_integrity()
        return {
            "node_id": self.node_id,
            "organization": self.organization,
            "port": self.port,
            "role": self.role,
            "chain_height": len(self.ledger.chain),
            "latest_block_hash": self.ledger.chain[-1].hash if self.ledger.chain else None,
            "integrity_valid": valid,
            "integrity_issues": issues,
            "registered_cameras": len(self.ledger.cameras),
            "registered_models": len(self.ledger.models),
            "recorded_intrusions": len(self.ledger.intrusions),
            "audit_logs_count": len(self.ledger.audit_logs),
            "active_security_alerts": len(self.ledger.security_alerts)
        }


def initialize_three_node_network(storage_dir: Optional[str] = None) -> Dict[str, BlockchainNode]:
    """
    Factory function to initialize the 3 distinct authority nodes:
    1. Border Police Node
    2. State Police Node
    3. Judiciary Node
    """
    border_police_node = BlockchainNode(
        node_id="BorderPolice-Node",
        organization="Border Security Force (BSF)",
        port=8001,
        role="Live CCTV Ingestion, Camera Signing & Perimeter Enforcement",
        storage_dir=storage_dir
    )

    state_police_node = BlockchainNode(
        node_id="StatePolice-Node",
        organization="State Police Department",
        port=8002,
        role="Regional Law Enforcement, Inter-Agency Coordination & Audit Monitoring",
        storage_dir=storage_dir
    )

    judiciary_node = BlockchainNode(
        node_id="Judiciary-Node",
        organization="High Court / Judicial Tribunal",
        port=8003,
        role="Forensic Evidence Verification, Model Certification & Chain of Custody Audit",
        storage_dir=storage_dir
    )

    # Cross-connect all 3 nodes in full mesh
    border_police_node.connect_peer(state_police_node)
    border_police_node.connect_peer(judiciary_node)

    state_police_node.connect_peer(border_police_node)
    state_police_node.connect_peer(judiciary_node)

    judiciary_node.connect_peer(border_police_node)
    judiciary_node.connect_peer(state_police_node)

    return {
        "border_police": border_police_node,
        "state_police": state_police_node,
        "judiciary": judiciary_node
    }
