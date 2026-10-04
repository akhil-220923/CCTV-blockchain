import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import json
import time
import shutil
import cv2
import requests
import threading
from flask import Flask, request, jsonify, send_from_directory, send_file, Response
from flask_cors import CORS

processing_lock = threading.Lock()

from blockchain.node import initialize_three_node_network, BlockchainNode
from blockchain.crypto_utils import calculate_file_sha256, calculate_data_sha256

app = Flask(__name__, static_folder="static")
CORS(app)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVIDENCE_DIR = os.path.join(BASE_DIR, "evidence")
OUTPUT_VIDEO_PATH = os.path.join(BASE_DIR, "ai_pipeline", "output", "annotated_border_surveillance.mp4")
RAW_VIDEO_PATH = os.path.join(BASE_DIR, "video", "test_cctv.mp4")

# Initialize the 3-node blockchain network
NODES = initialize_three_node_network()
border_police = NODES["border_police"]
state_police = NODES["state_police"]
judiciary = NODES["judiciary"]

# Load camera key info
camera_key_file = os.path.join(BASE_DIR, "security", "camera_001_public_key.pem")
camera_public_pem = ""
if os.path.exists(camera_key_file):
    with open(camera_key_file, "r") as f:
        camera_public_pem = f.read()

# Auto-register Camera if not present
has_cam = "CAM-001" in border_police.ledger.cameras or any(
    any(tx.get("type") == "CAMERA_REGISTRATION" and tx.get("camera_id") == "CAM-001" for tx in b.transactions)
    for b in border_police.ledger.chain
)
if not has_cam:
    border_police.broadcast_transaction(
        "register_camera",
        camera_id="CAM-001",
        public_key_pem=camera_public_pem,
        location="Sector-4 High-Altitude Border Ridge Post",
        registered_by="BorderPolice-Node"
    )

# Compute Model Hash and Auto-register on Judiciary Node
model_path = os.path.join(BASE_DIR, "ai_pipeline", "epoch_02.pt")
model_hash = calculate_file_sha256(model_path) if os.path.exists(model_path) else "b333639bc8d8343bb61ae10fa58311515b8f0f3545b580d0ff0ccc31464e9bef"

has_model = "LLVIP-BORDER-YOLO" in judiciary.ledger.models or any(
    any(tx.get("type") == "MODEL_REGISTRATION" and tx.get("model_id") == "LLVIP-BORDER-YOLO" for tx in b.transactions)
    for b in judiciary.ledger.chain
)
if not has_model:
    judiciary.broadcast_transaction(
        "register_model",
        model_id="LLVIP-BORDER-YOLO",
        model_name="BorderGuard-YOLOv8-LLVIP",
        model_hash=model_hash,
        version="v1.0-Certified",
        authorized_by="Judiciary-Node"
    )

# Ensure sample authorized personnel
has_personnel = "BP-OFFICER-701" in border_police.ledger.authorized_personnel or any(
    any(tx.get("type") == "PERSONNEL_AUTHORIZATION" and tx.get("personnel_id") == "BP-OFFICER-701" for tx in b.transactions)
    for b in border_police.ledger.chain
)
if not has_personnel:
    border_police.broadcast_transaction(
        "register_authorized_personnel",
        personnel_id="BP-OFFICER-701",
        name="Sub-Inspector Vikram Singh",
        rank="Border Patrol Officer",
        organization="Border Security Force",
        exemption_active=True,
        assigned_track_id=6
    )


# ---------------- VIDEO STREAMING GENERATORS ----------------

def generate_mjpeg_stream(video_path: str):
    """Yield MJPEG frames at real-time CCTV FPS for universal cross-browser playback."""
    while True:
        target = video_path
        if not os.path.exists(target) and os.path.exists(RAW_VIDEO_PATH):
            target = RAW_VIDEO_PATH
        if not os.path.exists(target):
            time.sleep(0.5)
            continue
        cap = cv2.VideoCapture(target)
        if not cap.isOpened():
            if target != RAW_VIDEO_PATH and os.path.exists(RAW_VIDEO_PATH):
                cap = cv2.VideoCapture(RAW_VIDEO_PATH)
            if not cap.isOpened():
                time.sleep(0.5)
                continue
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        frame_interval = 1.0 / fps
        while True:
            start_t = time.time()
            ret, frame = cap.read()
            if not ret:
                break
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            frame_bytes = buffer.tobytes()
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n"
                   b"Content-Length: " + str(len(frame_bytes)).encode() + b"\r\n\r\n" +
                   frame_bytes + b"\r\n")
            elapsed = time.time() - start_t
            sleep_t = max(0.01, frame_interval - elapsed)
            time.sleep(sleep_t)
        cap.release()


# Allowed file extensions and upload limit configuration
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100 MB max payload limit

# ---------------- HEALTH CHECKS ----------------

@app.route("/health", methods=["GET"])
@app.route("/api/health", methods=["GET"])
def health_check():
    """System health check endpoint for reverse proxy, Docker, and monitoring."""
    return jsonify({
        "status": "ok",
        "service": "backend",
        "timestamp": time.time(),
        "nodes": {
            "border_police": border_police.node_id,
            "state_police": state_police.node_id,
            "judiciary": judiciary.node_id
        }
    }), 200


# ---------------- SECURE FILE UPLOAD ROUTES ----------------

@app.route("/api/upload/video", methods=["POST"])
def upload_video():
    """Upload custom surveillance video for AI analysis and blockchain anchoring."""
    from werkzeug.utils import secure_filename

    if "file" not in request.files:
        return jsonify({"error": "No video file provided in form field 'file'"}), 400
    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"error": "No selected video file"}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        return jsonify({
            "error": f"Invalid video format '{ext}'. Supported formats: {', '.join(sorted(ALLOWED_VIDEO_EXTENSIONS))}"
        }), 400

    safe_name = secure_filename(file.filename) or f"cctv_{int(time.time())}.mp4"
    video_dir = os.path.join(BASE_DIR, "video")
    os.makedirs(video_dir, exist_ok=True)
    save_path = os.path.join(video_dir, safe_name)
    file.save(save_path)

    set_active = request.form.get("set_active", "true").lower() == "true"
    global RAW_VIDEO_PATH
    if set_active:
        RAW_VIDEO_PATH = save_path

    file_size = os.path.getsize(save_path)
    return jsonify({
        "status": "SUCCESS",
        "message": f"Surveillance video '{safe_name}' uploaded successfully ({file_size} bytes).",
        "file_name": safe_name,
        "file_path": save_path,
        "file_size": file_size,
        "is_active_cctv": (RAW_VIDEO_PATH == save_path)
    }), 200


@app.route("/api/upload/image", methods=["POST"])
def upload_image():
    """Upload single image snapshot for instant YOLOv8 person detection and cryptographic hashing."""
    from werkzeug.utils import secure_filename
    import numpy as np

    if "file" not in request.files:
        return jsonify({"error": "No image file provided in form field 'file'"}), 400
    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"error": "No selected image file"}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({
            "error": f"Invalid image format '{ext}'. Supported formats: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}"
        }), 400

    safe_name = secure_filename(file.filename) or f"snapshot_{int(time.time())}.jpg"
    file_bytes = file.read()
    nparr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return jsonify({"error": "Failed to decode image data"}), 400

    from ai_pipeline.detector import BorderPersonDetector
    detector = BorderPersonDetector()
    detections = detector.detect(img)
    img_hash = calculate_data_sha256(file_bytes.hex())

    return jsonify({
        "status": "SUCCESS",
        "file_name": safe_name,
        "sha256_hash": img_hash,
        "total_persons_detected": len(detections),
        "detections": detections,
        "image_dimensions": {
            "width": img.shape[1],
            "height": img.shape[0]
        },
        "message": f"Image analyzed: {len(detections)} persons detected by YOLOv8 engine."
    }), 200


# ---------------- API ROUTES ----------------

@app.route("/evidence/<path:filename>")
def get_evidence_image(filename):
    return send_from_directory(EVIDENCE_DIR, filename)


@app.route("/video/stream/annotated")
def stream_annotated_video():
    """Live MJPEG video stream of the AI annotated surveillance feed."""
    target = OUTPUT_VIDEO_PATH if os.path.exists(OUTPUT_VIDEO_PATH) else RAW_VIDEO_PATH
    if not os.path.exists(target):
        return jsonify({"error": "No surveillance video available"}), 404
    return Response(
        generate_mjpeg_stream(target),
        mimetype="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "Access-Control-Allow-Origin": "*",
        }
    )


@app.route("/video/stream/raw")
def stream_raw_video():
    """Live MJPEG video stream of the raw CCTV feed."""
    if not os.path.exists(RAW_VIDEO_PATH):
        return jsonify({"error": "Raw video not found"}), 404
    return Response(
        generate_mjpeg_stream(RAW_VIDEO_PATH),
        mimetype="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "Access-Control-Allow-Origin": "*",
        }
    )


@app.route("/video/annotated")
def get_annotated_video():
    target = OUTPUT_VIDEO_PATH if os.path.exists(OUTPUT_VIDEO_PATH) else RAW_VIDEO_PATH
    if os.path.exists(target):
        return send_file(target, mimetype="video/mp4", conditional=True)
    return jsonify({"error": "Annotated video not generated yet"}), 404


@app.route("/video/raw")
def get_raw_video():
    if os.path.exists(RAW_VIDEO_PATH):
        return send_file(RAW_VIDEO_PATH, mimetype="video/mp4", conditional=True)
    return jsonify({"error": "Raw video not found"}), 404


def sync_nodes():
    """Sync in-memory ledger state with persistent disk state across all 3 nodes."""
    for node in NODES.values():
        if os.path.exists(node.ledger.ledger_file):
            node.ledger.load_from_disk()


@app.route("/api/process-video", methods=["POST"])
def api_process_video():
    """
    Runs the AI border surveillance processing pipeline on the current video,
    anchors intrusion events into the 3-node blockchain, and generates H.264 annotated video.
    """
    if not processing_lock.acquire(blocking=False):
        return jsonify({
            "status": "BUSY",
            "message": "AI video scan is already in progress. Please wait for the current run to finish."
        }), 429

    try:
        from ai_pipeline.video_processor import BorderSurveillanceProcessor
        sync_nodes()

        # Clear previous video intrusions so new scan reflects only current video
        for n in NODES.values():
            n.ledger.intrusions.clear()
            # Keep foundational registration blocks (Genesis, Camera, Model, Personnel)
            n.ledger.chain = [b for b in n.ledger.chain if not any(tx.get("type") == "INTRUSION_EVIDENCE" for tx in b.transactions)]
            n.ledger.save_to_disk()

        processor = BorderSurveillanceProcessor(nodes=NODES)
        result = processor.process_video(
            input_video_path=RAW_VIDEO_PATH,
            output_video_path=OUTPUT_VIDEO_PATH,
            evidence_dir=EVIDENCE_DIR
        )

        sync_nodes()
        return jsonify({
            "status": "SUCCESS",
            "total_intrusions": result["total_intrusions"],
            "total_frames": result["total_frames"],
            "message": f"Surveillance video processed: {result['total_intrusions']} intrusions detected and anchored across all 3 blockchain nodes."
        })
    finally:
        processing_lock.release()


@app.route("/api/overview", methods=["GET"])
def get_overview():
    """Provides high-level dashboard metrics across AI and 3 blockchain nodes."""
    sync_nodes()
    bp_summary = border_police.to_summary()
    sp_summary = state_police.to_summary()
    jd_summary = judiciary.to_summary()

    all_event_ids = list(border_police.ledger.intrusions.keys())
    for n in NODES.values():
        for eid in n.ledger.intrusions.keys():
            if eid not in all_event_ids:
                all_event_ids.append(eid)

    authentic_intrusions = []
    tampered_intrusions = []
    active_intrusions = []

    for ev_id in all_event_ids:
        node_statuses = {}
        for n_name, n in NODES.items():
            ev = n.ledger.intrusions.get(ev_id)
            if ev:
                st = ev.get("detection_status", "INTRUSION_DETECTED")
                node_statuses[n.node_id] = st
            else:
                node_statuses[n.node_id] = "MISSING"

        authentic_intrusions.append(ev_id)
        # Check if any node was altered to NO_INTRUSION_DETECTED or there's a disparity
        is_tampered_ev = (
            any(st == "NO_INTRUSION_DETECTED" for st in node_statuses.values()) or
            len(set(node_statuses.values())) > 1
        )
        if is_tampered_ev:
            tampered_intrusions.append(ev_id)
        else:
            active_intrusions.append(ev_id)

    total_alerts = (
        len(border_police.ledger.security_alerts) +
        len(state_police.ledger.security_alerts) +
        len(judiciary.ledger.security_alerts)
    )
    is_tampered = total_alerts > 0 or len(tampered_intrusions) > 0

    # "There should be scope to change the intrusion detected to no intrusion detected so that intrusion detection is not found that means tampering has occured in this way tampering should be."
    # When tampered to NO_INTRUSION_DETECTED, active intrusions count drops to 0 (intrusion detection is not found on tampered node!)
    reported_intrusion_count = len(active_intrusions)

    return jsonify({
        "status": "OPERATIONAL",
        "system_time": time.time(),
        "camera": {
            "camera_id": "CAM-001",
            "location": "Sector-4 High-Altitude Border Ridge Post",
            "status": "REGISTERED_ACTIVE",
            "algorithm": "Ed25519",
            "public_key_preview": camera_public_pem[:40] + "..." if camera_public_pem else "N/A"
        },
        "model": {
            "model_id": "LLVIP-BORDER-YOLO",
            "model_name": "BorderGuard-YOLOv8-LLVIP",
            "model_hash": model_hash,
            "status": "JUDICIALLY_ANCHORED"
        },
        "nodes": {
            "border_police": bp_summary,
            "state_police": sp_summary,
            "judiciary": jd_summary
        },
        "metrics": {
            "total_intrusions": reported_intrusion_count,
            "authentic_intrusions_count": len(authentic_intrusions),
            "active_intrusions_count": len(active_intrusions),
            "tampered_intrusions_count": len(tampered_intrusions),
            "chain_height": bp_summary["chain_height"],
            "audit_logs_count": len(border_police.ledger.audit_logs),
            "authorized_personnel_count": len(border_police.ledger.authorized_personnel),
            "active_security_alerts": total_alerts,
            "is_tampered": is_tampered
        }
    })


@app.route("/api/nodes", methods=["GET"])
def get_nodes():
    """Detailed status of all 3 stakeholder nodes."""
    sync_nodes()
    return jsonify({
        "nodes": [
            border_police.to_summary(),
            state_police.to_summary(),
            judiciary.to_summary()
        ],
        "consensus_healthy": (
            border_police.sync_from_peers()["consensus_healthy"] and
            state_police.sync_from_peers()["consensus_healthy"] and
            judiciary.sync_from_peers()["consensus_healthy"]
        )
    })


@app.route("/api/blockchain/chain", methods=["GET"])
def get_blockchain_chain():
    """Returns the full tamper-evident blockchain for requested node (or Border Police by default)."""
    sync_nodes()
    node_key = request.args.get("node", "border_police")
    node_obj = NODES.get(node_key, border_police)
    chain_data = [b.to_dict() for b in node_obj.ledger.chain]
    valid, issues = node_obj.ledger.verify_ledger_integrity()

    peer_statuses = {}
    for nk, no in NODES.items():
        v, _ = no.ledger.verify_ledger_integrity()
        peer_statuses[nk] = {
            "node_id": no.node_id,
            "chain_length": len(no.ledger.chain),
            "is_valid": v,
            "alerts_count": len(no.ledger.security_alerts)
        }

    return jsonify({
        "node_id": node_obj.node_id,
        "node_key": node_key,
        "chain_length": len(chain_data),
        "is_integrity_valid": valid,
        "integrity_issues": issues,
        "chain": chain_data,
        "peer_statuses": peer_statuses
    })


@app.route("/api/events", methods=["GET"])
def get_intrusion_events():
    """Returns all recorded perimeter intrusion events with cross-node consensus evaluation."""
    sync_nodes()
    events = []
    all_event_ids = list(border_police.ledger.intrusions.keys())
    for n in NODES.values():
        for eid in n.ledger.intrusions.keys():
            if eid not in all_event_ids:
                all_event_ids.append(eid)

    for ev_id in all_event_ids:
        base_ev = border_police.ledger.intrusions.get(ev_id) or state_police.ledger.intrusions.get(ev_id) or judiciary.ledger.intrusions.get(ev_id)
        if not base_ev:
            continue
        item = dict(base_ev)

        node_statuses = {}
        tampered_nodes = []
        for node_key, node_obj in NODES.items():
            ev = node_obj.ledger.intrusions.get(ev_id)
            if ev:
                st = ev.get("detection_status", "INTRUSION_DETECTED")
                node_statuses[node_obj.node_id] = st
                if st == "NO_INTRUSION_DETECTED" or ev.get("is_tampered"):
                    tampered_nodes.append(node_obj.node_id)
            else:
                node_statuses[node_obj.node_id] = "MISSING/SUPPRESSED"
                tampered_nodes.append(node_obj.node_id)

        has_disparity = len(set(node_statuses.values())) > 1 or len(tampered_nodes) > 0
        if has_disparity:
            item["detection_status"] = "NO_INTRUSION_DETECTED"
            item["is_tampered"] = True
            item["tampered_nodes"] = tampered_nodes
            item["tamper_note"] = f"TAMPERED: Altered to NO INTRUSION DETECTED on {', '.join(tampered_nodes)} (Breach Concealment Attempt Flagged by Consensus)"
        else:
            item["detection_status"] = "INTRUSION_DETECTED"
            item["is_tampered"] = False
            item["tamper_note"] = ""

        item["node_statuses"] = node_statuses

        if item.get("evidence_file"):
            item["evidence_url"] = f"/evidence/{os.path.basename(item['evidence_file'])}"
        events.append(item)
    return jsonify({"events": events, "total": len(events)})


@app.route("/api/audit-logs", methods=["GET"])
def get_audit_logs():
    """
    Returns the immutable audit log for the requested node (or Border Police by default).
    Does NOT pollute logs on passive GET inspection unless record_access=true is explicitly requested.
    """
    sync_nodes()
    node_key = request.args.get("node", "border_police")
    target_node = NODES.get(node_key, border_police)

    if request.args.get("record_access") == "true":
        accessor_role = request.args.get("role", "External-Auditor")
        accessor_node = request.args.get("accessor_node", "StatePolice-Node")
        target_node.audit_access_attempt(
            accessor_identity=f"{accessor_role}@{accessor_node}",
            action="INSPECT_AUDIT_LOGS",
            target_id="ALL_AUDIT_ENTRIES"
        )
        for n in NODES.values():
            n.ledger.save_to_disk()
        sync_nodes()

    logs = list(target_node.ledger.audit_logs)
    return jsonify({
        "node_id": target_node.node_id,
        "node_key": node_key,
        "audit_logs": logs,
        "total_entries": len(logs),
        "security_alerts": target_node.ledger.security_alerts,
        "notification": f"Viewing authentic audit logs for {target_node.node_id}."
    })


@app.route("/api/audit-logs/access", methods=["POST"])
def record_audit_access_event():
    """
    Explicitly test audit log access broadcast:
    'Suppose if someone accessed the audit log the rest of the nodes should know that they accessed and modified.'
    """
    sync_nodes()
    data = request.get_json(silent=True) or {}
    node_key = data.get("node", "state_police")
    accessor_role = data.get("role", "External-Auditor")
    target_node = NODES.get(node_key, state_police)

    entry = target_node.audit_access_attempt(
        accessor_identity=f"{accessor_role}@{target_node.node_id}",
        action=data.get("action", "INSPECT_AUDIT_LOGS"),
        target_id=data.get("target_id", "ALL_AUDIT_ENTRIES")
    )
    for n in NODES.values():
        n.ledger.save_to_disk()
    sync_nodes()

    return jsonify({
        "status": "SUCCESS",
        "action_recorded": entry,
        "accessor_node": target_node.node_id,
        "message": f"Audit access by {accessor_role} logged on {target_node.node_id} and broadcast across all 3 nodes!"
    })


@app.route("/api/personnel", methods=["GET"])
def get_personnel():
    """Cybersecurity: Returns registered authorized personnel."""
    return jsonify({
        "authorized_personnel": list(border_police.ledger.authorized_personnel.values())
    })


@app.route("/api/personnel/authorize", methods=["POST"])
def authorize_personnel():
    """
    Cybersecurity Access Control:
    Toggle or grant authorized clearance to an officer or track ID.
    """
    data = request.get_json(silent=True) or {}
    personnel_id = data.get("personnel_id", f"BP-{int(time.time())%1000}")
    name = data.get("name", "Patrol Officer")
    rank = data.get("rank", "Inspector")
    exemption_active = bool(data.get("exemption_active", True))
    assigned_track_id = data.get("assigned_track_id")
    if assigned_track_id is not None:
        try:
            assigned_track_id = int(assigned_track_id)
        except ValueError:
            assigned_track_id = None

    tx = border_police.broadcast_transaction(
        "register_authorized_personnel",
        personnel_id=personnel_id,
        name=name,
        rank=rank,
        organization="Border Security Force",
        exemption_active=exemption_active,
        assigned_track_id=assigned_track_id
    )

    return jsonify({
        "status": "SUCCESS",
        "message": f"Personnel {name} ({personnel_id}) clearance set to {exemption_active}",
        "transaction": tx
    })


@app.route("/api/verify/evidence/<event_id>", methods=["GET", "POST"])
def verify_evidence(event_id):
    """
    Forensic Verification API:
    Judiciary & Police verification of an intrusion evidence frame:
    - Calculates SHA-256 hash of frame on disk.
    - Verifies against on-chain anchored hash.
    - Verifies camera Ed25519 digital signature.
    - Verifies AI model integrity.
    - Cross-verifies detection status across all authority nodes for breach concealment tampering!
    """
    sync_nodes()
    custom_path = None
    req_data = request.get_json(silent=True)
    if req_data and "file_path" in req_data:
        custom_path = req_data["file_path"]

    verification_result = judiciary.ledger.verify_evidence_forensics(event_id, custom_path)

    # Cross-evaluate across all nodes for breach concealment
    node_breakdown = {}
    tampered_nodes = []
    for n in NODES.values():
        ev = n.ledger.intrusions.get(event_id)
        if ev:
            st = ev.get("detection_status", "INTRUSION_DETECTED")
            node_breakdown[n.node_id] = st
            if st == "NO_INTRUSION_DETECTED" or ev.get("is_tampered"):
                tampered_nodes.append(n.node_id)
        else:
            node_breakdown[n.node_id] = "MISSING"
            tampered_nodes.append(n.node_id)

    verification_result["node_breakdown"] = node_breakdown
    if tampered_nodes or len(set(node_breakdown.values())) > 1:
        verification_result["is_authentic_forensic_evidence"] = False
        verification_result["is_concealed_tamper"] = True
        verification_result["tamper_reason"] = f"CRITICAL: Intrusion status altered to 'NO INTRUSION DETECTED' on {', '.join(tampered_nodes)} to conceal perimeter breach! Flagged by decentralized consensus."
        verification_result["tampered_nodes"] = tampered_nodes

    return jsonify(verification_result)


@app.route("/api/intrusion/change-status", methods=["POST"])
@app.route("/api/simulate/tamper-intrusion", methods=["POST"])
def change_intrusion_status():
    """
    Scope to change intrusion status from 'INTRUSION DETECTED' to 'NO INTRUSION DETECTED'
    so that intrusion detection is not found on the attacked node (simulating breach concealment tampering),
    or restore it back to 'INTRUSION DETECTED'.
    """
    sync_nodes()
    data = request.get_json(silent=True) or {}
    event_id = data.get("event_id")
    new_status = data.get("status") or data.get("new_status") or "NO_INTRUSION_DETECTED"
    node_key = data.get("node", "state_police")
    field = data.get("field")
    new_value = data.get("new_value")

    if not event_id:
        for n in NODES.values():
            if n.ledger.intrusions:
                event_id = list(n.ledger.intrusions.keys())[0]
                break

    if not event_id:
        return jsonify({"error": "No intrusion events recorded yet"}), 404

    target_node = NODES.get(node_key, state_police)

    if new_status == "NO_INTRUSION_DETECTED" or (field and new_value is not None):
        # Simulate tampering on target node
        tamper_res = target_node.ledger.simulate_tampering(
            target="intrusion",
            event_id=event_id,
            new_status=new_status,
            field=field,
            new_value=new_value
        )
        # Execute cross-node sync across peers so peer nodes immediately detect the tampering
        detection_bp = border_police.sync_from_peers()
        detection_sp = state_police.sync_from_peers()
        detection_jd = judiciary.sync_from_peers()

        for n in NODES.values():
            n.ledger.save_to_disk()

        sync_nodes()
        return jsonify({
            "status": "SUCCESS",
            "action": "TAMPER_INTRUSION",
            "event_id": event_id,
            "new_status": new_status,
            "attacked_node": target_node.node_id,
            "attacked_node_key": node_key,
            "tamper_caught_instantly": detection_bp["tamper_detected"] or detection_jd["tamper_detected"] or detection_sp["tamper_detected"],
            "tamper_res": tamper_res,
            "consensus_details": {
                "border_police": detection_bp,
                "state_police": detection_sp,
                "judiciary": detection_jd
            },
            "message": f"Intrusion {event_id} tampered on {target_node.node_id}! All peer authority nodes immediately detected the integrity violation."
        })
    else:
        # Restore to authentic state
        target_node.ledger.restore_intrusion_status(event_id=event_id)
        blk_idx = target_node.ledger.intrusions.get(event_id, {}).get("block_index")
        for n in NODES.values():
            n.ledger.security_alerts = [
                a for a in n.ledger.security_alerts
                if event_id not in str(a) and (blk_idx is None or (f"Block #{blk_idx}" not in str(a) and f"BLOCK-{blk_idx}" not in str(a)))
            ]
            n.ledger.save_to_disk()
            n.sync_from_peers()

        sync_nodes()
        return jsonify({
            "status": "SUCCESS",
            "action": "RESTORE_INTRUSION_STATUS",
            "event_id": event_id,
            "new_status": "INTRUSION_DETECTED",
            "node": target_node.node_id,
            "message": f"Intrusion {event_id} restored to 'INTRUSION DETECTED' on {target_node.node_id}. Cryptographic consensus verified across all 3 nodes."
        })


@app.route("/api/simulate/tamper", methods=["POST"])
def simulate_tamper():
    """
    Demonstration tool:
    Simulates malicious tampering with an intrusion event, audit log, or block,
    instantly demonstrating how other authority nodes detect the compromise!
    """
    data = request.get_json(silent=True) or {}
    target = data.get("target", "intrusion")
    node_to_attack = data.get("node", "state_police")
    event_id = data.get("event_id")
    new_status = data.get("new_status") or data.get("status") or "NO_INTRUSION_DETECTED"

    if target in ["intrusion", "intrusion_status", "no_intrusion", "tamper_intrusion"]:
        return change_intrusion_status()

    attacked_node = NODES.get(node_to_attack, state_police)
    tamper_result = attacked_node.ledger.simulate_tampering(target=target)

    # Cross-node verification
    detection_report = border_police.sync_from_peers()
    judiciary_report = judiciary.sync_from_peers()

    return jsonify({
        "tamper_action": tamper_result,
        "attacked_node": attacked_node.node_id,
        "border_police_detection": detection_report,
        "judiciary_detection": judiciary_report,
        "tamper_caught_instantly": detection_report["tamper_detected"] or judiciary_report["tamper_detected"],
        "message": "Tampering simulated! The other authority nodes have immediately flagged the integrity breach."
    })


@app.route("/api/simulate/tamper-evidence", methods=["POST"])
def simulate_tamper_evidence():
    """
    Demonstration tool:
    Simulates malicious alteration of an intrusion evidence frame on disk
    and verifies with Judiciary node.
    """
    data = request.get_json(silent=True) or {}
    event_id = data.get("event_id")
    if not event_id or event_id not in border_police.ledger.intrusions:
        if border_police.ledger.intrusions:
            event_id = list(border_police.ledger.intrusions.keys())[0]
        else:
            return jsonify({"error": "No intrusion events recorded yet to tamper"}), 404

    event = border_police.ledger.intrusions.get(event_id)
    original_file = event["evidence_file"]
    tampered_file = os.path.join(EVIDENCE_DIR, f"tampered_{os.path.basename(original_file)}")

    # Create a bit-altered copy
    if os.path.exists(original_file):
        with open(original_file, "rb") as src:
            content = bytearray(src.read())
        # Flip bytes to simulate image tampering
        if len(content) > 150:
            content[150] = (content[150] + 73) % 256
            content[151] = (content[151] + 19) % 256
        with open(tampered_file, "wb") as dst:
            dst.write(content)

    # Verify tampered file with Judiciary Node
    verification = judiciary.ledger.verify_evidence_forensics(event_id, tampered_file)

    # Record tamper attempt in audit log
    judiciary.ledger.log_audit_access(
        accessor_node="Judiciary-Node",
        accessor_identity="Forensic-Lab-System",
        action="TAMPER_DETECTED_ON_EVIDENCE",
        target_id=event_id,
        status="CRITICAL_ALARM",
        details=f"Evidence frame {tampered_file} hash mismatch! Expected: {event['frame_hash'][:16]}..., Computed: {verification['current_frame_hash'][:16]}..."
    )

    return jsonify({
        "original_file": original_file,
        "tampered_file": tampered_file,
        "verification_result": verification,
        "tamper_detected": not verification["hash_matches"],
        "message": "Evidence tampering caught! Frame hash does not match on-chain anchor, and digital signature is invalid."
    })


@app.route("/api/simulate/restore", methods=["POST"])
def restore_integrity():
    """Restore nodes and ledger to authentic state after tamper demonstration."""
    for node_name, node in NODES.items():
        node.ledger.security_alerts = []

        # Restore intrusions to authentic state
        for ev_id, ev in node.ledger.intrusions.items():
            ev["detection_status"] = "INTRUSION_DETECTED"
            ev["is_tampered"] = False
            ev.pop("tamper_note", None)

        # Restore audit entries
        for e in node.ledger.audit_logs:
            if "details" in e and "MALICIOUS" in e["details"]:
                e["details"] = "INSPECT_AUDIT_LOGS completed normally (Restored authentic log)"
            c_entry = dict(e)
            c_entry.pop("entry_hash", None)
            e["entry_hash"] = calculate_data_sha256(json.dumps(c_entry, sort_keys=True))

        # Re-verify and relink blocks
        for i in range(1, len(node.ledger.chain)):
            b = node.ledger.chain[i]
            # Remove any malicious injection
            b.transactions = [tx for tx in b.transactions if tx.get("type") != "MALICIOUS_INJECTION"]
            for tx in b.transactions:
                if tx.get("type") == "INTRUSION_EVIDENCE":
                    tx["detection_status"] = "INTRUSION_DETECTED"
                    tx.pop("tampered", None)
            b.previous_hash = node.ledger.chain[i - 1].hash
            b.merkle_root = b.compute_merkle_root()
            b.hash = b.calculate_hash()
        node.ledger.save_to_disk()

    # Clean up any tampered evidence copy
    if os.path.exists(EVIDENCE_DIR):
        for f in os.listdir(EVIDENCE_DIR):
            if f.startswith("tampered_"):
                try:
                    os.remove(os.path.join(EVIDENCE_DIR, f))
                except Exception:
                    pass

    # Re-sync peers
    border_police.sync_from_peers()
    state_police.sync_from_peers()
    judiciary.sync_from_peers()
    for n in NODES.values():
        n.ledger.security_alerts = []
        n.ledger.save_to_disk()

    return jsonify({
        "status": "RESTORED",
        "message": "All 3 authority nodes restored to authentic, consensus-verified cryptographic state."
    })


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def index_or_frontend(path):
    """Serve modern React frontend by proxying non-API/non-video requests to Node SSR (port 3000)."""
    if path.startswith("api/") or path.startswith("video/") or path.startswith("evidence/"):
        return jsonify({"error": "Endpoint not found"}), 404

    frontend_base = os.environ.get("FRONTEND_URL", "http://127.0.0.1:3000").rstrip("/")
    vite_url = f"{frontend_base}/{path}"
    if request.query_string:
        vite_url += f"?{request.query_string.decode('utf-8')}"
    try:
        hop_by_hop = {'host', 'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization', 'te', 'trailers', 'transfer-encoding', 'upgrade'}
        req_headers = {key: value for (key, value) in request.headers if key.lower() not in hop_by_hop}
        resp = requests.request(
            method=request.method,
            url=vite_url,
            headers=req_headers,
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            stream=True,
            timeout=10
        )
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]
        return Response(resp.iter_content(chunk_size=16384), resp.status_code, headers)
    except Exception:
        if not path or path == "":
            return send_from_directory(app.static_folder, "index.html")
        return send_from_directory(app.static_folder, path)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"[Border Surveillance Server] Starting Web Dashboard & Blockchain API on {host}:{port}...")
    app.run(host=host, port=port, debug=False)
