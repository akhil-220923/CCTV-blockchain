import os
import cv2
import json
import time
import numpy as np
from typing import Dict, List, Any, Optional

from .detector import BorderPersonDetector
from .tracker import ByteTracker
from .zone_manager import RestrictedZoneManager
from blockchain.node import initialize_three_node_network, BlockchainNode
from blockchain.crypto_utils import (
    calculate_file_sha256,
    calculate_data_sha256,
    load_private_key_from_file,
    load_public_key_from_file,
    sign_data,
    verify_signature
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class BorderSurveillanceProcessor:
    """
    End-to-End Border Surveillance Processor integrating:
    1. Camera Registration & Ed25519 Stream Signing
    2. Model Hashing & Blockchain Anchoring
    3. Person Detection & ByteTrack Multi-Object Tracking
    4. Restricted Zone Intrusion Detection with Anti-Spam De-duplication
    5. Cybersecurity Access Control (Authorized Personnel Exemption)
    6. 3-Node Blockchain Ledger (Border Police, State Police, Judiciary)
    7. Exact Intrusion Frame Capture & Video Evidence Export
    """

    def __init__(
        self,
        camera_id: str = "CAM-001",
        camera_private_key_path: str = "security/camera_001_private_key.pem",
        camera_public_key_path: str = "security/camera_001_public_key.pem",
        camera_location: str = "Sector-4 North Ridge Perimeter Post",
        nodes: Optional[Dict[str, BlockchainNode]] = None
    ):
        self.camera_id = camera_id
        self.camera_location = camera_location
        self.camera_private_key_path = camera_private_key_path if os.path.isabs(camera_private_key_path) else os.path.join(BASE_DIR, camera_private_key_path)
        self.camera_public_key_path = camera_public_key_path if os.path.isabs(camera_public_key_path) else os.path.join(BASE_DIR, camera_public_key_path)

        # Load camera cryptographic keys
        if not os.path.exists(self.camera_private_key_path) or not os.path.exists(self.camera_public_key_path):
            raise FileNotFoundError(f"Camera key pair not found at {self.camera_private_key_path} or {self.camera_public_key_path}!")

        self.camera_private_key = load_private_key_from_file(self.camera_private_key_path)
        with open(self.camera_public_key_path, "r") as f:
            self.camera_public_key_pem = f.read()

        # Initialize or connect 3-node blockchain network
        self.nodes = nodes if nodes is not None else initialize_three_node_network()
        self.primary_node = self.nodes["border_police"]

        # Register camera on-chain
        print(f"[Blockchain] Registering Camera {self.camera_id} across 3 authority nodes...")
        self.primary_node.broadcast_transaction(
            "register_camera",
            camera_id=self.camera_id,
            public_key_pem=self.camera_public_key_pem,
            location=self.camera_location,
            registered_by=self.primary_node.node_id
        )

        # Initialize AI Detector and anchor certified model hash on-chain
        self.detector = BorderPersonDetector()
        self.model_hash = self.detector.get_model_hash()
        print(f"[Blockchain] Anchoring AI Model (Hash: {self.model_hash[:16]}...) on-chain...")
        self.nodes["judiciary"].broadcast_transaction(
            "register_model",
            model_id="LLVIP-BORDER-YOLO",
            model_name="BorderGuard-YOLOv8-LLVIP",
            model_hash=self.model_hash,
            version="v1.0-Production",
            authorized_by=self.nodes["judiciary"].node_id
        )

        # Initialize ByteTrack multi-object tracker
        self.tracker = ByteTracker(track_thresh=0.15, high_thresh=0.25, match_thresh=0.80, max_time_lost=30)

        # Initialize Restricted Zone Manager
        self.zone_manager = RestrictedZoneManager()

        # Cybersecurity: Register pre-authorized border patrol officer (Exemption Demo)
        # Demonstrates that authorized personnel entering restricted zone are NOT flagged as intruders
        self.nodes["border_police"].broadcast_transaction(
            "register_authorized_personnel",
            personnel_id="BP-OFFICER-701",
            name="Sub-Inspector Vikram Singh",
            rank="Border Patrol Officer",
            organization="Border Security Force",
            exemption_active=True,
            assigned_track_id=6  # Track #6 enters restricted zone legitimately
        )
        self.zone_manager.authorize_personnel(
            track_id=6,
            personnel_id="BP-OFFICER-701",
            name="Sub-Inspector Vikram Singh",
            rank="Border Patrol Officer"
        )

        self.recorded_events: List[Dict[str, Any]] = []

    def process_video(
        self,
        input_video_path: str = "video/test_cctv.mp4",
        output_video_path: str = "ai_pipeline/output/annotated_border_surveillance.mp4",
        evidence_dir: str = "evidence",
        max_frames: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute full video surveillance pipeline:
        Reads CCTV video, performs detection, ByteTrack tracking, zone breach validation,
        cryptographic signing, blockchain anchoring, and annotated video generation.
        """
        input_video_path = input_video_path if os.path.isabs(input_video_path) else os.path.join(BASE_DIR, input_video_path)
        output_video_path = output_video_path if os.path.isabs(output_video_path) else os.path.join(BASE_DIR, output_video_path)
        evidence_dir = evidence_dir if os.path.isabs(evidence_dir) else os.path.join(BASE_DIR, evidence_dir)

        os.makedirs(os.path.dirname(os.path.abspath(output_video_path)), exist_ok=True)
        os.makedirs(evidence_dir, exist_ok=True)

        cap = cv2.VideoCapture(input_video_path)
        if not cap.isOpened():
            raise IOError(f"Could not open input video: {input_video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Dynamically adapt restricted zone polygon to current video resolution
        self.zone_manager.adapt_to_resolution(width, height)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

        frame_num = 0
        intrusion_count = 0
        active_intruders_in_frame = 0

        print(f"[Video Processor] Starting video processing: {total_frames} frames @ {fps:.1f} FPS")

        while True:
            ret, frame = cap.read()
            if not ret or (max_frames is not None and frame_num >= max_frames):
                break

            timestamp_seconds = frame_num / fps
            mins = int(timestamp_seconds // 60)
            secs = timestamp_seconds % 60
            timestamp_str = f"{mins:02d}:{secs:06.3f}"

            # 1. Run Person Detection
            detections = self.detector.detect(frame)

            # 2. Run ByteTrack Tracking
            active_tracks = self.tracker.update(detections)

            frame_has_active_intrusion = False
            active_intruder_count = 0

            active_track_ids = {t.track_id for t in active_tracks}

            # 3. Process each track through Restricted Zone Manager
            for track in active_tracks:
                track_id = track.track_id
                x1, y1, x2, y2 = track.tlbr.astype(int)
                bbox = (x1, y1, x2, y2)

                zone_result = self.zone_manager.process_track(
                    track_id=track_id,
                    bbox=bbox,
                    frame_number=frame_num,
                    timestamp_str=timestamp_str,
                    active_track_ids=active_track_ids
                )

                status = zone_result["status"]
                color = zone_result["color_bgr"]
                label = zone_result["display_label"]

                if status in ["INTRUSION_ALERT", "INTRUSION_ACTIVE"]:
                    frame_has_active_intrusion = True
                    active_intruder_count += 1

                # If first time entering restricted zone -> capture snapshot and anchor on blockchain!
                if zone_result["trigger_new_intrusion"]:
                    intrusion_count += 1
                    event_id = f"INTRUSION-DET-{intrusion_count:03d}"
                    evidence_filename = f"intrusion_{self.camera_id}_track_{track_id}_frame_{frame_num:04d}.jpg"
                    evidence_path = os.path.join(evidence_dir, evidence_filename)

                    # Save EXACT frame image evidence
                    cv2.imwrite(evidence_path, frame)

                    # Cryptographic Evidence Provenance
                    frame_sha256 = calculate_file_sha256(evidence_path)
                    camera_sig = sign_data(self.camera_private_key, frame_sha256)

                    print(f"\n🚨 [CRITICAL ALERT] Intrusion detected in Restricted Zone!")
                    print(f"   Event ID       : {event_id}")
                    print(f"   Track ID       : #{track_id}")
                    print(f"   Frame Number   : {frame_num} ({timestamp_str})")
                    print(f"   Evidence File  : {evidence_path}")
                    print(f"   Frame SHA-256  : {frame_sha256}")
                    print(f"   Camera Sig     : {camera_sig[:24]}...")
                    print(f"   Model Hash     : {self.model_hash[:24]}...")
                    print(f"   Anchoring on 3-Node Blockchain...")

                    # Anchor on blockchain across Border Police, State Police, and Judiciary
                    on_chain_event = self.primary_node.broadcast_transaction(
                        "record_intrusion_event",
                        event_id=event_id,
                        camera_id=self.camera_id,
                        track_id=track_id,
                        frame_number=frame_num,
                        timestamp_str=timestamp_str,
                        frame_hash=frame_sha256,
                        camera_signature=camera_sig,
                        model_hash=self.model_hash,
                        zone_id=self.zone_manager.zone_id,
                        evidence_file=evidence_path
                    )
                    self.recorded_events.append(on_chain_event)

                # Draw track bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                # Label background pill
                (lbl_w, lbl_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                cv2.rectangle(frame, (x1, max(y1 - 22, 0)), (x1 + lbl_w + 6, max(y1, 22)), color, -1)
                cv2.putText(
                    frame,
                    label,
                    (x1 + 3, max(y1 - 6, 16)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 0) if color != (0, 0, 255) else (255, 255, 255),
                    2
                )

            # 4. Draw Restricted Zone Overlay
            frame = self.zone_manager.draw_zone_overlay(frame, active_alert=frame_has_active_intrusion)

            # 5. Draw HUD Surveillance Telemetry
            hud_height = 36 if width < 600 else 50
            scale = 0.40 if width < 600 else 0.55
            thickness = 1 if width < 600 else 2
            cv2.rectangle(frame, (0, 0), (width, hud_height), (15, 15, 20), -1)

            # HUD items
            cam_text = f"CAM: {self.camera_id}"
            time_text = f"T: {timestamp_str}"
            intrusions_text = f"INTRUSIONS: {intrusion_count}"

            cv2.putText(frame, cam_text, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 255, 200), thickness)
            cv2.putText(frame, time_text, (int(width * 0.35), 22), cv2.FONT_HERSHEY_SIMPLEX, scale, (255, 255, 255), thickness)
            cv2.putText(
                frame,
                intrusions_text,
                (int(width * 0.65), 22),
                cv2.FONT_HERSHEY_SIMPLEX,
                scale,
                (0, 0, 255) if intrusion_count > 0 else (0, 255, 0),
                thickness
            )

            # Flashing intrusion alarm banner if active breach
            if frame_has_active_intrusion:
                banner_y2 = (hud_height + 25) if width < 600 else 85
                cv2.rectangle(frame, (0, hud_height), (width, banner_y2), (0, 0, 220), -1)
                alert_text = f"[ALERT] BREACH ACTIVE ({active_intruder_count})" if width < 600 else f"[ALERT] PERIMETER BREACH ACTIVE : {active_intruder_count} INTRUDER(S) IN RESTRICTED ZONE"
                cv2.putText(frame, alert_text, (12 if width < 600 else width // 2 - 320, hud_height + 18), cv2.FONT_HERSHEY_SIMPLEX, scale, (255, 255, 255), thickness)

            writer.write(frame)
            frame_num += 1

            if frame_num % 50 == 0:
                print(f"[Video Processor] Processed {frame_num}/{total_frames} frames... ({int(frame_num/total_frames*100)}%)")

        cap.release()
        writer.release()

        # Convert to universal web-compatible H.264 MP4 (+faststart) using imageio_ffmpeg
        try:
            import subprocess
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            temp_mp4 = output_video_path + ".raw_mp4v.mp4"
            if os.path.exists(temp_mp4):
                os.remove(temp_mp4)
            os.rename(output_video_path, temp_mp4)
            cmd = [
                ffmpeg_exe, "-y",
                "-i", temp_mp4,
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                output_video_path
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            if os.path.exists(temp_mp4):
                os.remove(temp_mp4)
            print(f"   [Video Processor] Successfully encoded Web-compatible H.264 MP4 ({output_video_path})")
        except Exception as e:
            print(f"   [Video Processor] Warning during FFmpeg H.264 encoding: {e}")

        print(f"\n[Video Processor] Video processing completed!")
        print(f"   Output Video       : {output_video_path}")
        print(f"   Total Frames       : {frame_num}")
        print(f"   Total Intrusions   : {intrusion_count}")
        print(f"   Blockchain Height  : {len(self.primary_node.ledger.chain)} blocks")

        return {
            "output_video": output_video_path,
            "total_frames": frame_num,
            "total_intrusions": intrusion_count,
            "events": self.recorded_events,
            "blockchain_summary": self.primary_node.to_summary()
        }
