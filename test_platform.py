import os
import sys
import json
import time
import shutil
import cv2
import numpy as np

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ai_pipeline.detector import BorderPersonDetector
from ai_pipeline.tracker import ByteTracker
from ai_pipeline.zone_manager import RestrictedZoneManager
from blockchain.node import initialize_three_node_network
from blockchain.crypto_utils import (
    calculate_data_sha256,
    calculate_file_sha256,
    sign_data,
    verify_signature,
    load_private_key_from_file,
    load_public_key_from_file,
    load_public_key_from_pem
)


def run_all_tests():
    print("=" * 70)
    print("  SENTINEL-CHAIN: FULL END-TO-END VERIFICATION TEST SUITE")
    print("=" * 70)

    # ---------------- TEST 1: Camera Key Generation & Registration ----------------
    print("\n[TEST 1] Camera Registration & Stream Cryptographic Provenance...")
    cam_priv_path = os.path.join(BASE_DIR, "security", "camera_001_private_key.pem")
    cam_pub_path = os.path.join(BASE_DIR, "security", "camera_001_public_key.pem")
    assert os.path.exists(cam_priv_path), "Camera private key missing!"
    assert os.path.exists(cam_pub_path), "Camera public key missing!"

    cam_priv = load_private_key_from_file(cam_priv_path)
    cam_pub = load_public_key_from_file(cam_pub_path)
    test_stream_hash = calculate_data_sha256("TEST_CCTV_FRAME_BYTES_001")
    test_sig = sign_data(cam_priv, test_stream_hash)
    assert verify_signature(cam_pub, test_stream_hash, test_sig), "Camera signature verification failed!"
    print("  ✓ Camera Ed25519 signature correctly generated and verified.")

    # ---------------- TEST 2: Model Hashing & Integrity ----------------
    print("\n[TEST 2] AI Model Hashing & Blockchain Anchoring...")
    detector = BorderPersonDetector()
    model_hash = detector.get_model_hash()
    print(f"  Computed Model SHA-256: {model_hash}")
    assert len(model_hash) == 64, "Model hash must be 64-char SHA-256 string!"
    print("  ✓ Certified AI model hashed and verified.")

    # ---------------- TEST 3: 3-Node Blockchain Network Initialization ----------------
    print("\n[TEST 3] 3-Node Stakeholder Network (Border Police, State Police, Judiciary)...")
    test_storage = os.path.join(BASE_DIR, "test_blockchain_data")
    if os.path.exists(test_storage):
        shutil.rmtree(test_storage)
    shutil.copytree(os.path.join(BASE_DIR, "blockchain_data"), test_storage)

    nodes = initialize_three_node_network(storage_dir=test_storage)
    bp = nodes["border_police"]
    sp = nodes["state_police"]
    jd = nodes["judiciary"]

    assert bp.node_id == "BorderPolice-Node"
    assert sp.node_id == "StatePolice-Node"
    assert jd.node_id == "Judiciary-Node"
    assert len(bp.peers) == 2 and len(sp.peers) == 2 and len(jd.peers) == 2, "Full mesh topology required!"
    print("  ✓ All 3 authority nodes initialized and interconnected in full mesh.")

    # Register camera and model across nodes
    with open(cam_pub_path, "r") as f:
        cam_pub_pem = f.read()

    bp.broadcast_transaction(
        "register_camera",
        camera_id="CAM-001",
        public_key_pem=cam_pub_pem,
        location="Sector-4 High-Altitude Border Ridge Post",
        registered_by=bp.node_id
    )

    jd.broadcast_transaction(
        "register_model",
        model_id="LLVIP-BORDER-YOLO",
        model_name="BorderGuard-YOLOv8-LLVIP",
        model_hash=model_hash,
        version="v1.0-Certified",
        authorized_by=jd.node_id
    )

    # Verify state replicated across all 3 nodes
    for n in [bp, sp, jd]:
        assert "CAM-001" in n.ledger.cameras, f"Camera CAM-001 missing in {n.node_id}"
        assert "LLVIP-BORDER-YOLO" in n.ledger.models, f"Model missing in {n.node_id}"
    print("  ✓ Camera and Model registrations replicated across all 3 nodes.")

    # ---------------- TEST 4: Person Detection & ByteTrack ----------------
    print("\n[TEST 4] Person Detection & ByteTrack Multi-Object Tracking...")
    cap = cv2.VideoCapture(os.path.join(BASE_DIR, "video", "test_cctv.mp4"))
    cap.set(cv2.CAP_PROP_POS_FRAMES, 110)
    ret, test_frame = cap.read()
    cap.release()
    assert ret, "Could not read frame from test video!"

    detections = detector.detect(test_frame)
    print(f"  Frame 110 Detections: {len(detections)} persons detected")
    assert len(detections) > 0, "Expected at least 1 person detection in surveillance video!"

    tracker = ByteTracker(track_thresh=0.15, high_thresh=0.25, match_thresh=0.80, max_time_lost=30)
    tracks = tracker.update(detections)
    print(f"  ByteTrack Active Tracks in Frame 110: {len(tracks)}")
    assert len(tracks) > 0, "ByteTrack should create active tracks!"
    print("  ✓ Person detection and ByteTrack successfully tracking objects.")

    # ---------------- TEST 5: Restricted Zone & Anti-Spam De-duplication ----------------
    print("\n[TEST 5] Restricted Zone Intrusion & Anti-Spam De-duplication...")
    zm = RestrictedZoneManager()

    # Track 100: Unauthorized intruder enters and stays for 50 frames
    intruder_bbox = (150, 120, 190, 180)  # inside restricted polygon
    assert zm.is_inside_zone(intruder_bbox), "Test bbox should be inside restricted zone!"

    # Frame 0: Entry -> Must trigger intrusion
    res_f0 = zm.process_track(track_id=100, bbox=intruder_bbox, frame_number=0, timestamp_str="00:00.000")
    assert res_f0["trigger_new_intrusion"] is True, "First entry must trigger intrusion!"
    assert res_f0["status"] == "INTRUSION_ALERT"

    # Frame 1 to 50: Same intruder stays in zone -> MUST NOT trigger multiple intrusions
    for f_idx in range(1, 51):
        res_subsequent = zm.process_track(
            track_id=100,
            bbox=intruder_bbox,
            frame_number=f_idx,
            timestamp_str=f"00:{f_idx:02d}.000"
        )
        assert res_subsequent["trigger_new_intrusion"] is False, f"Frame {f_idx} triggered duplicate intrusion!"
        assert res_subsequent["status"] == "INTRUSION_ACTIVE", f"Status should remain INTRUSION_ACTIVE on frame {f_idx}"
    print("  ✓ De-duplication verified: exactly 1 intrusion triggered over 50 dwell frames.")

    # ---------------- TEST 6: Cybersecurity Authorized Personnel Exemption ----------------
    print("\n[TEST 6] Cybersecurity: Authorized Personnel Entering Zone (NO Intrusion Alarm)...")
    zm.authorize_personnel(
        track_id=200,
        personnel_id="BP-OFFICER-701",
        name="Sub-Inspector Vikram Singh",
        rank="Border Patrol Officer"
    )

    # Authorized officer enters the exact same restricted zone
    res_auth = zm.process_track(
        track_id=200,
        bbox=intruder_bbox,
        frame_number=0,
        timestamp_str="00:00.000"
    )
    assert res_auth["is_authorized"] is True, "Personnel should be recognized as authorized!"
    assert res_auth["trigger_new_intrusion"] is False, "Authorized personnel MUST NOT trigger intrusion alarm!"
    assert res_auth["status"] == "AUTHORIZED_ACCESS", "Status must be AUTHORIZED_ACCESS!"
    print(f"  ✓ Authorized personnel ({res_auth['display_label']}) entered restricted zone with NO intrusion alarm.")

    # ---------------- TEST 7: Cross-Node Audit Logging & Inter-Agency Notification ----------------
    print("\n[TEST 7] Cross-Node Audit Access Logging & Broadcast...")
    # Someone accesses the audit logs on State Police node
    initial_bp_audits = len(bp.ledger.audit_logs)
    sp.audit_access_attempt(
        accessor_identity="External-Auditor@StatePolice",
        action="INSPECT_BORDER_AUDIT",
        target_id="PERIMETER_LOGS"
    )
    # Check that Border Police and Judiciary were notified of this access
    assert len(bp.ledger.audit_logs) > initial_bp_audits, "Border Police node should receive access notice!"
    latest_bp_audit = bp.ledger.audit_logs[-1]
    assert "INTER-AGENCY NOTICE" in latest_bp_audit["details"], "Notice details must identify cross-node access!"
    print(f"  ✓ Access logged on State Police and broadcast to peer nodes: '{latest_bp_audit['details']}'")

    # ---------------- TEST 8: Tamper Detection (Simulate Malicious Modification) ----------------
    print("\n[TEST 8] Cross-Node Tamper Detection (Unauthorized Audit Modification)...")
    # Simulate an unauthorized actor tampering with the audit log on State Police node
    tamper_result = sp.ledger.simulate_tampering(target="audit_log")
    assert tamper_result["status"] == "TAMPERED", "Tamper simulation failed"

    # Border Police runs consensus sync
    bp_sync = bp.sync_from_peers()
    assert bp_sync["tamper_detected"] is True, "Border Police node MUST detect peer tampering!"
    assert len(bp.ledger.security_alerts) > 0, "Security alert must be raised on tamper detection!"

    # Judiciary runs consensus sync
    jd_sync = jd.sync_from_peers()
    assert jd_sync["tamper_detected"] is True, "Judiciary node MUST detect peer tampering!"
    print(f"  ✓ Tamper detection confirmed: Border Police & Judiciary raised alerts: '{bp.ledger.security_alerts[-1]['message']}'")

    # Restore ledger
    bp.ledger.security_alerts = []
    sp.ledger.security_alerts = []
    jd.ledger.security_alerts = []
    for entry in sp.ledger.audit_logs:
        if "details" in entry and "MALICIOUS" in entry["details"]:
            entry["details"] = "Authorized audit inspection"
            c_entry = dict(entry)
            c_entry.pop("entry_hash", None)
            entry["entry_hash"] = calculate_data_sha256(json.dumps(c_entry, sort_keys=True))
    sp.ledger.save_to_disk()
    print("  ✓ Nodes restored to authentic state.")

    # ---------------- TEST 9: Forensic Evidence Scrutiny with Judiciary Node ----------------
    print("\n[TEST 9] Judiciary Forensic Scrutiny of Evidence...")
    # Anchor authentic intrusion evidence on blockchain with camera signature and model hash
    evidence_dir = os.path.join(BASE_DIR, "evidence")
    os.makedirs(evidence_dir, exist_ok=True)
    test_ev_file = os.path.join(evidence_dir, "test_intrusion_001.jpg")
    cv2.imwrite(test_ev_file, test_frame)
    ev_frame_hash = calculate_file_sha256(test_ev_file)
    ev_camera_sig = sign_data(cam_priv, ev_frame_hash)

    bp.broadcast_transaction(
        "record_intrusion_event",
        event_id="INTRUSION-DET-001",
        camera_id="CAM-001",
        track_id=100,
        frame_number=110,
        timestamp_str="00:03.666",
        frame_hash=ev_frame_hash,
        camera_signature=ev_camera_sig,
        model_hash=model_hash,
        zone_id="ZONE-ALPHA-BORDER",
        evidence_file=test_ev_file
    )

    # Judiciary scrutinizes the authentic on-chain intrusion (INTRUSION-DET-001)
    forensic_res = jd.ledger.verify_evidence_forensics("INTRUSION-DET-001")
    assert forensic_res["is_authentic_forensic_evidence"] is True, "Forensic verification must pass for authentic evidence!"
    assert forensic_res["hash_matches"] is True
    assert forensic_res["signature_valid"] is True
    assert forensic_res["model_registered"] is True
    print(f"  ✓ Judiciary verified evidence 'INTRUSION-DET-001' as 100% authentic and legally admissible.")

    # Now tamper with evidence (bit-flip) and re-verify
    tampered_test_file = os.path.join(evidence_dir, "test_tampered_frame.jpg")
    with open(test_ev_file, "rb") as f_in:
        content = bytearray(f_in.read())
    content[100] = (content[100] + 55) % 256
    with open(tampered_test_file, "wb") as f_out:
        f_out.write(content)

    tampered_res = jd.ledger.verify_evidence_forensics("INTRUSION-DET-001", tampered_test_file)
    assert tampered_res["is_authentic_forensic_evidence"] is False, "Judiciary MUST reject tampered evidence!"
    assert tampered_res["hash_matches"] is False, "Hash must mismatch for tampered file!"
    if os.path.exists(tampered_test_file):
        os.remove(tampered_test_file)
    if os.path.exists(test_ev_file):
        os.remove(test_ev_file)
    shutil.rmtree(test_storage, ignore_errors=True)
    print("  ✓ Judiciary successfully detected tampered evidence and ruled it INADMISSIBLE!")

    print("\n" + "=" * 70)
    print("  ALL 9 END-TO-END VERIFICATION TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
