import os
import json
import time
import copy
from typing import List, Dict, Any, Optional, Tuple
from .block import Block
from .crypto_utils import (
    calculate_data_sha256,
    calculate_file_sha256,
    verify_signature,
    load_public_key_from_pem,
    load_public_key_from_file
)


class BlockchainLedger:
    """
    Decentralized tamper-evident ledger for Border Surveillance.
    Maintains Camera Registry, AI Model Registry, Authorized Personnel,
    Intrusion Evidence Records, and Immutable Audit Logs.
    """

    def __init__(self, node_id: str = "BorderPolice-Node", storage_dir: str = "blockchain_data"):
        self.node_id = node_id
        self.storage_dir = os.path.join(storage_dir, node_id)
        os.makedirs(self.storage_dir, exist_ok=True)
        self.ledger_file = os.path.join(self.storage_dir, "ledger.json")

        self.chain: List[Block] = []
        self.pending_transactions: List[Dict[str, Any]] = []

        # State stores
        self.cameras: Dict[str, Dict[str, Any]] = {}
        self.models: Dict[str, Dict[str, Any]] = {}
        self.authorized_personnel: Dict[str, Dict[str, Any]] = {}
        self.intrusions: Dict[str, Dict[str, Any]] = {}
        self.audit_logs: List[Dict[str, Any]] = []
        self.security_alerts: List[Dict[str, Any]] = []
        self._last_loaded_mtime: float = 0.0

        if os.path.exists(self.ledger_file):
            self.load_from_disk()
        else:
            self.create_genesis_block()
            self.save_to_disk()

    def create_genesis_block(self):
        """Initialize genesis block with genesis governance transactions."""
        genesis_tx = [{
            "type": "GENESIS",
            "timestamp": 1700000000.0,
            "message": "Border Surveillance Blockchain Network Initialized",
            "participating_nodes": [
                "BorderPolice-Node",
                "StatePolice-Node",
                "Judiciary-Node"
            ],
            "consensus": "Proof-of-Authority-Multisig"
        }]
        genesis_block = Block(
            index=0,
            transactions=genesis_tx,
            previous_hash="0" * 64,
            timestamp=1700000000.0,
            validator_node="System-Genesis"
        )
        self.chain = [genesis_block]

    def register_camera(
        self,
        camera_id: str,
        public_key_pem: str,
        location: str,
        registered_by: str = "BorderPolice-Node"
    ) -> Dict[str, Any]:
        """Register a CCTV camera on the blockchain with its cryptographic public key."""
        tx = {
            "type": "CAMERA_REGISTRATION",
            "camera_id": camera_id,
            "public_key_pem": public_key_pem,
            "location": location,
            "registered_by": registered_by,
            "timestamp": time.time(),
            "status": "ACTIVE"
        }
        self.cameras[camera_id] = tx
        self.pending_transactions.append(tx)
        self.mine_pending_transactions(validator_node=registered_by)
        self.log_audit_access(
            accessor_node=self.node_id,
            accessor_identity=registered_by,
            action="CAMERA_REGISTRATION",
            target_id=camera_id,
            status="SUCCESS",
            details=f"Camera {camera_id} registered at {location}"
        )
        return tx

    def register_model(
        self,
        model_id: str,
        model_name: str,
        model_hash: str,
        version: str = "v1.0-LLVIP",
        authorized_by: str = "Judiciary-Node"
    ) -> Dict[str, Any]:
        """Anchor certified AI model hash into blockchain as cryptographic proof of integrity."""
        tx = {
            "type": "MODEL_REGISTRATION",
            "model_id": model_id,
            "model_name": model_name,
            "model_hash": model_hash,
            "version": version,
            "authorized_by": authorized_by,
            "timestamp": time.time(),
            "status": "VERIFIED_ACTIVE"
        }
        self.models[model_id] = tx
        self.pending_transactions.append(tx)
        self.mine_pending_transactions(validator_node=authorized_by)
        self.log_audit_access(
            accessor_node=self.node_id,
            accessor_identity=authorized_by,
            action="MODEL_REGISTRATION",
            target_id=model_id,
            status="SUCCESS",
            details=f"Model {model_name} (hash: {model_hash[:16]}...) anchored by {authorized_by}"
        )
        return tx

    def register_authorized_personnel(
        self,
        personnel_id: str,
        name: str,
        rank: str,
        organization: str = "Border Security Force",
        exemption_active: bool = True,
        assigned_track_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Cybersecurity Access Control:
        Register authorized personnel with access rights to restricted border zones.
        When these individuals enter the restricted zone, they are NOT flagged as intruders.
        """
        tx = {
            "type": "PERSONNEL_AUTHORIZATION",
            "personnel_id": personnel_id,
            "name": name,
            "rank": rank,
            "organization": organization,
            "exemption_active": exemption_active,
            "assigned_track_id": assigned_track_id,
            "timestamp": time.time(),
            "updated_by": self.node_id
        }
        self.authorized_personnel[personnel_id] = tx
        self.pending_transactions.append(tx)
        self.mine_pending_transactions(validator_node=self.node_id)
        self.log_audit_access(
            accessor_node=self.node_id,
            accessor_identity=self.node_id,
            action="PERSONNEL_AUTHORIZATION",
            target_id=personnel_id,
            status="SUCCESS",
            details=f"Authorized personnel {name} ({rank}) access status set to {exemption_active}"
        )
        return tx

    def record_intrusion_event(
        self,
        event_id: str,
        camera_id: str,
        track_id: int,
        frame_number: int,
        timestamp_str: str,
        frame_hash: str,
        camera_signature: str,
        model_hash: str,
        zone_id: str = "ZONE-ALPHA-BORDER",
        evidence_file: str = ""
    ) -> Dict[str, Any]:
        """
        Record verified intrusion event on the blockchain with full cryptographic provenance:
        1. Camera signature verified against registered camera public key.
        2. Model hash verified against registered model.
        """
        # Validate camera registration
        camera_info = self.cameras.get(camera_id)
        camera_verified = False
        if camera_info:
            try:
                pub_key = load_public_key_from_pem(camera_info["public_key_pem"])
                camera_verified = verify_signature(pub_key, frame_hash, camera_signature)
            except Exception as e:
                camera_verified = False

        # Validate model registration
        model_verified = any(m["model_hash"] == model_hash for m in self.models.values())

        tx = {
            "type": "INTRUSION_EVIDENCE",
            "event_id": event_id,
            "camera_id": camera_id,
            "track_id": track_id,
            "frame_number": frame_number,
            "video_timestamp": timestamp_str,
            "frame_hash": frame_hash,
            "camera_signature": camera_signature,
            "model_hash": model_hash,
            "zone_id": zone_id,
            "evidence_file": evidence_file,
            "detection_status": "INTRUSION_DETECTED",
            "camera_verified": camera_verified,
            "model_verified": model_verified,
            "recorded_at": time.time(),
            "reporting_node": self.node_id
        }

        tx_to_mine = copy.deepcopy(tx)
        self.pending_transactions.append(tx_to_mine)
        block = self.mine_pending_transactions(validator_node=self.node_id)
        tx_record = dict(tx)
        tx_record["block_index"] = block.index
        tx_record["block_hash"] = block.hash
        tx_record["detection_status"] = "INTRUSION_DETECTED"
        self.intrusions[event_id] = tx_record

        # Add audit log for intrusion recording
        self.log_audit_access(
            accessor_node=self.node_id,
            accessor_identity="AI-Inference-Engine",
            action="RECORD_INTRUSION",
            target_id=event_id,
            status="ANCHORED_ON_CHAIN",
            details=f"Intrusion {event_id} (Track #{track_id}) committed into Block #{block.index}"
        )
        return tx_record

    def log_audit_access(
        self,
        accessor_node: str,
        accessor_identity: str,
        action: str,
        target_id: str,
        status: str = "SUCCESS",
        details: str = "",
        timestamp: Optional[float] = None,
        audit_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Tamper-evident audit access logging:
        Whenever someone accesses or queries the audit log, evidence, or records,
        an audit record is created and distributed across all nodes.
        If someone modifies the log, other nodes detect the hash disparity.
        """
        ts = timestamp if timestamp is not None else time.time()
        aid = audit_id if audit_id is not None else f"AUDIT-{int(ts*1000)}-{len(self.audit_logs)}"
        audit_entry = {
            "audit_id": aid,
            "timestamp": ts,
            "accessor_node": accessor_node,
            "accessor_identity": accessor_identity,
            "action": action,
            "target_id": target_id,
            "status": status,
            "details": details,
            "prev_log_hash": self.audit_logs[-1]["entry_hash"] if self.audit_logs else "0"*64
        }
        entry_hash = calculate_data_sha256(json.dumps(audit_entry, sort_keys=True))
        audit_entry["entry_hash"] = entry_hash
        self.audit_logs.append(audit_entry)
        self.save_to_disk()
        return audit_entry

    def mine_pending_transactions(self, validator_node: str = None, timestamp: float = None) -> Block:
        """Mine pending transactions into a new cryptographic block."""
        if not self.pending_transactions:
            return self.chain[-1]

        validator = validator_node if validator_node else self.node_id
        previous_block = self.chain[-1]
        new_block = Block(
            index=len(self.chain),
            transactions=copy.deepcopy(self.pending_transactions),
            previous_hash=previous_block.hash,
            timestamp=timestamp if timestamp is not None else time.time(),
            validator_node=validator
        )
        self.chain.append(new_block)
        self.pending_transactions = []
        self.save_to_disk()
        return new_block

    def receive_block(self, block: Block) -> bool:
        """Receive a mined block from a peer validator node and replicate state."""
        if block.index < len(self.chain):
            return True

        if block.index != len(self.chain):
            return False
        if block.previous_hash != self.chain[-1].hash:
            return False
        if not block.verify_integrity():
            return False

        # Apply state updates from block transactions
        for tx in block.transactions:
            t_type = tx.get("type")
            if t_type == "CAMERA_REGISTRATION":
                self.cameras[tx["camera_id"]] = dict(tx)
            elif t_type == "MODEL_REGISTRATION":
                self.models[tx["model_id"]] = dict(tx)
            elif t_type == "PERSONNEL_AUTHORIZATION":
                self.authorized_personnel[tx["personnel_id"]] = dict(tx)
            elif t_type == "INTRUSION_EVIDENCE":
                ev_id = tx["event_id"]
                item = dict(tx)
                item["block_index"] = block.index
                item["block_hash"] = block.hash
                item.setdefault("detection_status", "INTRUSION_DETECTED")
                self.intrusions[ev_id] = item

        self.chain.append(copy.deepcopy(block))
        self.save_to_disk()
        return True

    def verify_ledger_integrity(self) -> Tuple[bool, List[str]]:
        """
        Verify the end-to-end cryptographic integrity of the blockchain:
        1. Genesis block correctness.
        2. Block hash computation matches stored hash.
        3. Previous block hash matches block's previous_hash.
        4. Merkle root integrity.
        """
        issues = []
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            prev = self.chain[i - 1]

            if not current.verify_integrity():
                issues.append(f"Block #{current.index} integrity compromised: hash or Merkle root invalid.")

            if current.previous_hash != prev.hash:
                issues.append(f"Block #{current.index} previous_hash ({current.previous_hash[:10]}...) does not match Block #{prev.index} hash ({prev.hash[:10]}...).")

        return len(issues) == 0, issues

    def verify_evidence_forensics(self, event_id: str, current_file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Forensic evidence verification for Judiciary / Police:
        1. Read stored intrusion event from blockchain.
        2. Compute current SHA-256 of the evidence file on disk.
        3. Verify against on-chain anchored frame_hash.
        4. Verify camera Ed25519 signature against registered camera public key.
        5. Verify AI model hash against registered model.
        """
        self.log_audit_access(
            accessor_node=self.node_id,
            accessor_identity=f"Forensic-Auditor@{self.node_id}",
            action="VERIFY_EVIDENCE",
            target_id=event_id,
            status="INSPECTED",
            details=f"Evidence verification initiated for event {event_id}"
        )

        event = self.intrusions.get(event_id)
        if not event:
            return {
                "verified": False,
                "error": f"Event {event_id} not found in blockchain ledger."
            }

        file_to_check = current_file_path if current_file_path else event.get("evidence_file", "")
        file_exists = os.path.exists(file_to_check)
        if not file_exists and file_to_check:
            base_filename = os.path.basename(file_to_check)
            repo_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            candidate_paths = [
                os.path.join(repo_base, "evidence", base_filename),
                os.path.join("evidence", base_filename),
                os.path.join("/app/evidence", base_filename),
            ]
            for candidate in candidate_paths:
                if os.path.exists(candidate):
                    file_to_check = candidate
                    file_exists = True
                    break
        current_hash = calculate_file_sha256(file_to_check) if file_exists else "FILE_MISSING"

        hash_matches = (current_hash == event["frame_hash"])

        # Verify camera signature
        camera_id = event["camera_id"]
        camera_info = self.cameras.get(camera_id)
        signature_valid = False
        if camera_info and file_exists:
            try:
                pub_key = load_public_key_from_pem(camera_info["public_key_pem"])
                signature_valid = verify_signature(pub_key, current_hash, event["camera_signature"])
            except Exception:
                signature_valid = False

        # Verify model registration
        model_registered = any(m["model_hash"] == event["model_hash"] for m in self.models.values())

        detection_status = event.get("detection_status", "INTRUSION_DETECTED")
        is_concealed_tamper = (detection_status == "NO_INTRUSION_DETECTED" or event.get("is_tampered", False))

        is_authentic = hash_matches and signature_valid and model_registered and not is_concealed_tamper

        tamper_reason = ""
        if is_concealed_tamper:
            tamper_reason = "CRITICAL: Intrusion status altered to 'NO INTRUSION DETECTED' to conceal perimeter breach!"
        elif not hash_matches:
            tamper_reason = "Hash mismatch: Evidence image modified on disk."
        elif not signature_valid:
            tamper_reason = "Camera signature invalid: Digital provenance failed."
        elif not model_registered:
            tamper_reason = "Model not anchored: Model hash not found in Judiciary registry."

        return {
            "event_id": event_id,
            "camera_id": camera_id,
            "track_id": event["track_id"],
            "video_timestamp": event["video_timestamp"],
            "evidence_file": file_to_check,
            "file_exists": file_exists,
            "stored_frame_hash": event["frame_hash"],
            "current_frame_hash": current_hash,
            "hash_matches": hash_matches,
            "camera_signature": event["camera_signature"],
            "signature_valid": signature_valid,
            "model_hash": event["model_hash"],
            "model_registered": model_registered,
            "detection_status": detection_status,
            "is_concealed_tamper": is_concealed_tamper,
            "tamper_reason": tamper_reason,
            "block_index": event.get("block_index", -1),
            "is_authentic_forensic_evidence": is_authentic
        }

    def detect_cross_node_tampering(
        self,
        remote_chain_dicts: List[Dict[str, Any]],
        remote_node_id: str,
        remote_audit_logs: Optional[List[Dict[str, Any]]] = None,
        remote_intrusions: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Cross-Node Tamper Detection:
        If someone accessed the audit log, blocks, or intrusion events on another node and modified them,
        this method detects the divergence and flags the tamper incident across the remaining nodes.
        'There should be scope to change the intrusion detected to no intrusion detected so that
        intrusion detection is not found that means tampering has occured in this way tampering should be.'
        """
        alerts = []
        is_tampered = False

        # 1. Check Block Hash Disparities
        min_len = min(len(self.chain), len(remote_chain_dicts))
        for i in range(min_len):
            local_block = self.chain[i]
            remote_dict = remote_chain_dicts[i]

            if local_block.hash != remote_dict.get("hash"):
                is_tampered = True
                alert = {
                    "alert_id": f"TAMPER-ALERT-BLK-{int(time.time()*1000)}-{i}",
                    "timestamp": time.time(),
                    "severity": "CRITICAL",
                    "target_type": "BLOCK",
                    "block_index": i,
                    "local_node": self.node_id,
                    "remote_node": remote_node_id,
                    "local_hash": local_block.hash,
                    "remote_hash": remote_dict.get("hash"),
                    "message": f"CRITICAL INTEGRITY BREACH: Block #{i} hash disparity detected! Block modified on {remote_node_id} or local ledger.",
                    "detected_by": [self.node_id]
                }
                alerts.append(alert)
                if not any(a.get("block_index") == i and a.get("remote_node") == remote_node_id for a in self.security_alerts):
                    self.security_alerts.append(alert)
                    self.log_audit_access(
                        accessor_node=self.node_id,
                        accessor_identity="Consensus-Monitor",
                        action="TAMPER_DETECTED",
                        target_id=f"BLOCK-{i}",
                        status="TAMPER_ALARM_RAISED",
                        details=alert["message"]
                    )

        # 2. Check Intrusion Detection Disparities (e.g. Changed to 'NO INTRUSION DETECTED' to conceal breach)
        if remote_intrusions is not None:
            for ev_id, local_ev in self.intrusions.items():
                local_status = local_ev.get("detection_status", "INTRUSION_DETECTED")
                if ev_id in remote_intrusions:
                    rem_ev = remote_intrusions[ev_id]
                    rem_status = rem_ev.get("detection_status", "INTRUSION_DETECTED")

                    # Check for status concealment
                    status_disparity = (local_status == "INTRUSION_DETECTED" and rem_status == "NO_INTRUSION_DETECTED") or (local_status == "NO_INTRUSION_DETECTED" and rem_status == "INTRUSION_DETECTED")

                    # Check for data field disparity (e.g. altered track ID or frame hash)
                    data_mismatches = []
                    for k in ["frame_hash", "track_id", "camera_signature", "frame_number", "video_timestamp"]:
                        lv = local_ev.get(k)
                        rv = rem_ev.get(k)
                        if lv is not None and rv is not None and lv != rv:
                            data_mismatches.append(f"{k} ('{lv}' vs '{rv}')")

                    if status_disparity or data_mismatches:
                        is_tampered = True
                        if status_disparity:
                            if local_status == "INTRUSION_DETECTED" and rem_status == "NO_INTRUSION_DETECTED":
                                msg = f"CRITICAL INTEGRITY BREACH: Intrusion {ev_id} was maliciously changed from 'INTRUSION DETECTED' to 'NO INTRUSION DETECTED' on {remote_node_id}! Attempted concealment of perimeter breach caught by consensus."
                            else:
                                msg = f"CRITICAL INTEGRITY BREACH: Intrusion {ev_id} status disparity! Local node ({self.node_id}) has 'NO INTRUSION DETECTED' while authentic consensus node ({remote_node_id}) has 'INTRUSION DETECTED'. Concealment attempt flagged by consensus."
                            target_type = "INTRUSION_CONCEALMENT"
                        else:
                            msg = f"CRITICAL INTEGRITY BREACH: Intrusion {ev_id} data modified on {remote_node_id}! Disparity: {', '.join(data_mismatches)}. Caught by consensus."
                            target_type = "INTRUSION_DATA_MODIFICATION"

                        alert = {
                            "alert_id": f"TAMPER-ALERT-INTRUSION-{int(time.time()*1000)}-{ev_id}",
                            "timestamp": time.time(),
                            "severity": "CRITICAL",
                            "target_type": target_type,
                            "event_id": ev_id,
                            "local_node": self.node_id,
                            "remote_node": remote_node_id,
                            "message": msg,
                            "detected_by": [self.node_id]
                        }
                        alerts.append(alert)
                        if not any(a.get("event_id") == ev_id and a.get("remote_node") == remote_node_id for a in self.security_alerts):
                            self.security_alerts.append(alert)
                            self.log_audit_access(
                                accessor_node=self.node_id,
                                accessor_identity="Consensus-Monitor",
                                action="INTRUSION_TAMPER_DETECTED",
                                target_id=ev_id,
                                status="TAMPER_ALARM_RAISED",
                                details=alert["message"]
                            )
                elif local_status == "INTRUSION_DETECTED":
                    is_tampered = True
                    alert = {
                        "alert_id": f"TAMPER-ALERT-INTRUSION-DEL-{int(time.time()*1000)}-{ev_id}",
                        "timestamp": time.time(),
                        "severity": "CRITICAL",
                        "target_type": "INTRUSION_DELETION",
                        "event_id": ev_id,
                        "local_node": self.node_id,
                        "remote_node": remote_node_id,
                        "message": f"CRITICAL INTEGRITY BREACH: Intrusion {ev_id} was deleted/suppressed on {remote_node_id}! Concealment caught by consensus.",
                        "detected_by": [self.node_id]
                    }
                    alerts.append(alert)
                    if not any(a.get("event_id") == ev_id and a.get("remote_node") == remote_node_id for a in self.security_alerts):
                        self.security_alerts.append(alert)
                        self.log_audit_access(
                            accessor_node=self.node_id,
                            accessor_identity="Consensus-Monitor",
                            action="INTRUSION_TAMPER_DETECTED",
                            target_id=ev_id,
                            status="TAMPER_ALARM_RAISED",
                            details=alert["message"]
                        )

        # 3. Check Audit Log Disparities & Unauthorized Alterations
        if remote_audit_logs is not None:
            local_audit_map = {e["audit_id"]: e for e in self.audit_logs}
            for rem_entry in remote_audit_logs:
                rem_id = rem_entry.get("audit_id")
                rem_copy = dict(rem_entry)
                stored_rem_hash = rem_copy.pop("entry_hash", "")
                computed_rem_hash = calculate_data_sha256(json.dumps(rem_copy, sort_keys=True))

                if stored_rem_hash != computed_rem_hash or "MALICIOUS" in str(rem_entry.get("details", "")):
                    is_tampered = True
                    alert = {
                        "alert_id": f"TAMPER-ALERT-AUDIT-{int(time.time()*1000)}",
                        "timestamp": time.time(),
                        "severity": "CRITICAL",
                        "target_type": "AUDIT_LOG",
                        "audit_id": rem_id,
                        "local_node": self.node_id,
                        "remote_node": remote_node_id,
                        "message": f"CRITICAL INTEGRITY BREACH: Audit log entry {rem_id} on {remote_node_id} was modified! Consensus rejected this unauthorized tampering.",
                        "detected_by": [self.node_id]
                    }
                    alerts.append(alert)
                    if not any(a.get("audit_id") == rem_id and a.get("remote_node") == remote_node_id for a in self.security_alerts):
                        self.security_alerts.append(alert)
                        self.log_audit_access(
                            accessor_node=self.node_id,
                            accessor_identity="Consensus-Monitor",
                            action="AUDIT_TAMPER_DETECTED",
                            target_id=rem_id or "AUDIT_LOG",
                            status="TAMPER_ALARM_RAISED",
                            details=alert["message"]
                        )
                    break

        return {
            "integrity_intact": not is_tampered,
            "tamper_detected": is_tampered,
            "tampered_items_count": len(alerts),
            "alerts": alerts
        }

    def simulate_tampering(self, target: str = "intrusion", index: int = 1, **kwargs) -> Dict[str, Any]:
        """
        Demonstration helper:
        Simulate an unauthorized entity maliciously modifying an intrusion, block, or audit log
        so other nodes immediately catch and report the tamper.
        Supports:
        - target="intrusion": Changes 'Intrusion Detected' to 'No Intrusion Detected' so intrusion detection is not found!
        - target="block": Maliciously injects unauthorized transaction into a block.
        - target="audit_log": Maliciously alters an audit entry.
        """
        if target in ["intrusion", "intrusion_status", "no_intrusion", "tamper_intrusion"]:
            target_id = kwargs.get("event_id") or (list(self.intrusions.keys())[0] if self.intrusions else "INTRUSION-DET-001")
            new_status = kwargs.get("new_status", "NO_INTRUSION_DETECTED")

            if target_id in self.intrusions:
                ev = self.intrusions[target_id]
                old_status = ev.get("detection_status", "INTRUSION_DETECTED")
                field = kwargs.get("field")
                new_val = kwargs.get("new_value")
                blk_idx = ev.get("block_index")

                if field and new_val is not None:
                    old_val = ev.get(field)
                    ev[field] = new_val
                    ev["is_tampered"] = True
                    ev["tamper_note"] = f"TAMPERED: Field '{field}' modified to '{new_val}'"
                    if blk_idx is not None and blk_idx < len(self.chain):
                        blk = self.chain[blk_idx]
                        for tx in blk.transactions:
                            if tx.get("event_id") == target_id:
                                tx[field] = new_val
                                tx["tampered"] = True
                        blk.merkle_root = blk.compute_merkle_root()
                        blk.hash = blk.calculate_hash()

                    self.log_audit_access(
                        accessor_node=self.node_id,
                        accessor_identity="Unauthorized-Insider",
                        action="ALTER_INTRUSION_DATA",
                        target_id=target_id,
                        status="UNAUTHORIZED_OVERWRITE",
                        details=f"Intrusion {target_id} field '{field}' modified from '{old_val}' to '{new_val}'"
                    )
                    self.save_to_disk()
                    return {
                        "status": "TAMPERED",
                        "target": "intrusion_field",
                        "event_id": target_id,
                        "field": field,
                        "previous_value": old_val,
                        "new_value": new_val,
                        "message": f"Intrusion {target_id} field '{field}' maliciously altered to '{new_val}' on {self.node_id}!"
                    }

                ev["detection_status"] = new_status
                ev["is_tampered"] = (new_status == "NO_INTRUSION_DETECTED")
                if new_status == "NO_INTRUSION_DETECTED":
                    ev["tamper_note"] = "TAMPERED: Altered to NO INTRUSION DETECTED to conceal breach"
                else:
                    ev.pop("tamper_note", None)

                # Also alter the transaction in the block where the intrusion was recorded
                blk_idx = ev.get("block_index")
                if blk_idx is not None and blk_idx < len(self.chain):
                    blk = self.chain[blk_idx]
                    for tx in blk.transactions:
                        if tx.get("event_id") == target_id:
                            tx["detection_status"] = new_status
                            tx["tampered"] = (new_status == "NO_INTRUSION_DETECTED")
                    blk.merkle_root = blk.compute_merkle_root()
                    blk.hash = blk.calculate_hash()

                self.log_audit_access(
                    accessor_node=self.node_id,
                    accessor_identity="Unauthorized-Insider",
                    action="ALTER_INTRUSION_RECORD",
                    target_id=target_id,
                    status="UNAUTHORIZED_OVERWRITE",
                    details=f"Intrusion {target_id} detection altered from '{old_status}' to '{new_status}' (Concealment attempt)"
                )
                self.save_to_disk()
                return {
                    "status": "TAMPERED",
                    "target": "intrusion",
                    "event_id": target_id,
                    "previous_status": old_status,
                    "new_status": new_status,
                    "message": f"Intrusion {target_id} altered from '{old_status}' to '{new_status}'. Intrusion detection is not found on {self.node_id}, simulating breach concealment tampering!"
                }
            return {"status": "NOOP", "message": f"Intrusion {target_id} not found to tamper"}

        elif target == "block" and len(self.chain) > 1:
            target_block = self.chain[min(index, len(self.chain) - 1)]
            target_block.transactions.append({
                "type": "MALICIOUS_INJECTION",
                "attacker": "Unauthorized-Intruder",
                "timestamp": time.time(),
                "payload": "TAMPERED_RECORD_DELETION"
            })
            self.save_to_disk()
            return {
                "status": "TAMPERED",
                "target": "block",
                "block_index": target_block.index,
                "message": f"Block #{target_block.index} maliciously modified. Hash integrity is now compromised!"
            }
        elif target == "audit_log" and self.audit_logs:
            target_entry = self.audit_logs[-1]
            target_entry["details"] = "MALICIOUSLY_ALTERED_AUDIT_DETAILS (Tampered)"
            self.save_to_disk()
            return {
                "status": "TAMPERED",
                "target": "audit_log",
                "audit_id": target_entry["audit_id"],
                "message": f"Audit entry {target_entry['audit_id']} altered without proper authorization!"
            }
        return {"status": "NOOP", "message": "Nothing to tamper"}

    def restore_intrusion_status(self, event_id: str = "INTRUSION-DET-001") -> Dict[str, Any]:
        """Restore an altered intrusion back to authentic INTRUSION_DETECTED state and recompute block hashes."""
        if event_id in self.intrusions:
            ev = self.intrusions[event_id]
            ev["detection_status"] = "INTRUSION_DETECTED"
            ev["is_tampered"] = False
            ev.pop("tamper_note", None)

            blk_idx = ev.get("block_index")
            if blk_idx is not None and blk_idx < len(self.chain):
                blk = self.chain[blk_idx]
                for tx in blk.transactions:
                    if tx.get("event_id") == event_id:
                        tx["detection_status"] = "INTRUSION_DETECTED"
                        tx.pop("tampered", None)
                for i in range(1, len(self.chain)):
                    self.chain[i].previous_hash = self.chain[i - 1].hash
                    self.chain[i].merkle_root = self.chain[i].compute_merkle_root()
                    self.chain[i].hash = self.chain[i].calculate_hash()

            self.security_alerts = []
            self.save_to_disk()
            return {"status": "RESTORED", "event_id": event_id}
        return {"status": "NOT_FOUND"}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "chain_length": len(self.chain),
            "chain": [b.to_dict() for b in self.chain],
            "cameras": self.cameras,
            "models": self.models,
            "authorized_personnel": self.authorized_personnel,
            "intrusions": self.intrusions,
            "audit_logs": self.audit_logs,
            "security_alerts": self.security_alerts
        }

    def save_to_disk(self):
        """Persist blockchain ledger to disk."""
        data = self.to_dict()
        with open(self.ledger_file, "w") as f:
            json.dump(data, f, indent=2)
        try:
            self._last_loaded_mtime = os.path.getmtime(self.ledger_file)
        except OSError:
            pass

    def load_from_disk(self):
        """Load blockchain ledger from disk if modified."""
        if not os.path.exists(self.ledger_file):
            return
        try:
            mtime = os.path.getmtime(self.ledger_file)
            if hasattr(self, "_last_loaded_mtime") and self._last_loaded_mtime and mtime <= self._last_loaded_mtime and self.chain:
                return
        except OSError:
            pass

        with open(self.ledger_file, "r") as f:
            data = json.load(f)
        self.chain = [Block.from_dict(b) for b in data.get("chain", [])]
        self.cameras = data.get("cameras", {})
        self.models = data.get("models", {})
        self.authorized_personnel = data.get("authorized_personnel", {})
        self.intrusions = data.get("intrusions", {})
        for ev in self.intrusions.values():
            if not ev.get("detection_status"):
                ev["detection_status"] = "INTRUSION_DETECTED"
            if "is_tampered" not in ev:
                ev["is_tampered"] = (ev.get("detection_status") == "NO_INTRUSION_DETECTED")
        self.audit_logs = data.get("audit_logs", [])
        self.security_alerts = data.get("security_alerts", [])
        try:
            self._last_loaded_mtime = os.path.getmtime(self.ledger_file)
        except OSError:
            pass
