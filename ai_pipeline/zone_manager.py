import cv2
import numpy as np
import time
from typing import List, Tuple, Dict, Any, Optional, Set


class RestrictedZoneManager:
    """
    Manages restricted perimeter zones, intrusion detection, stateful de-duplication,
    and cybersecurity authorized personnel exemptions.
    """

    def __init__(
        self,
        polygon_points: Optional[List[Tuple[int, int]]] = None,
        zone_id: str = "ZONE-ALPHA-BORDER",
        zone_name: str = "Sector-4 High Security Restricted Border Line"
    ):
        self.zone_id = zone_id
        self.zone_name = zone_name

        # Default polygon: tactical border exclusion zone across CCTV frame
        if polygon_points is None:
            # Default covering the tactical corridor
            self.polygon = np.array([
                [15, 90],
                [465, 90],
                [465, 260],
                [15, 260]
            ], dtype=np.int32)
        else:
            self.polygon = np.array(polygon_points, dtype=np.int32)

        # Stateful tracking per track_id:
        # track_id -> {
        #   'in_zone': bool,
        #   'intrusion_reported': bool,
        #   'first_intrusion_frame': int,
        #   'first_intrusion_timestamp': str,
        #   'is_authorized': bool,
        #   'personnel_id': Optional[str],
        #   'duration_frames': int
        # }
        self.track_states: Dict[int, Dict[str, Any]] = {}

        # Set of track IDs or personnel badges authorized for perimeter access
        self.authorized_track_ids: Set[int] = set()
        self.authorized_personnel_map: Dict[str, Any] = {}

        # Spatial-temporal intrusion sessions for bulletproof anti-spam / de-duplication:
        # Ensures that lingering or re-tracked persons never trigger multiple alarms.
        self.active_intrusion_sessions: List[Dict[str, Any]] = []

    def set_zone_polygon(self, points: List[Tuple[int, int]]):
        """Update the restricted zone polygon dynamically."""
        self.polygon = np.array(points, dtype=np.int32)

    def authorize_personnel(self, track_id: int, personnel_id: str, name: str, rank: str):
        """
        Cybersecurity Access Control:
        Assign authorized personnel credentials to a track ID.
        If an authorized person enters the restricted zone, they are NOT flagged as an intruder.
        """
        self.authorized_track_ids.add(track_id)
        self.authorized_personnel_map[track_id] = {
            "personnel_id": personnel_id,
            "name": name,
            "rank": rank,
            "authorized_at": time.time()
        }

    def revoke_authorization(self, track_id: int):
        """Revoke authorized clearance from a track ID."""
        self.authorized_track_ids.discard(track_id)
        self.authorized_personnel_map.pop(track_id, None)

    def adapt_to_resolution(self, width: int, height: int):
        """Adapt zone polygon dynamically based on video resolution."""
        if width <= 500:
            self.polygon = np.array([
                [15, int(height * 0.25)],
                [width - 15, int(height * 0.25)],
                [width - 15, int(height * 0.72)],
                [15, int(height * 0.72)]
            ], dtype=np.int32)
        else:
            # Realistic restricted road perimeter zone for CCTV surveillance (1280x720)
            self.polygon = np.array([
                [int(width * 0.375), int(height * 0.66)],    # (480, 475) along sidewalk/curb
                [int(width * 0.765), int(height * 0.715)],   # (980, 515) curb boundary
                [int(width * 0.8125), int(height * 0.972)],  # (1040, 700) road perimeter edge
                [int(width * 0.328), int(height * 0.903)]    # (420, 650) road edge near parked car
            ], dtype=np.int32)

    def is_inside_zone(self, bbox: Tuple[int, int, int, int]) -> bool:
        """
        Test if a person is inside the restricted zone using their ground contact point
        (bottom-center: ((x1 + x2)/2, y2)) or centroid ((x1 + x2)/2, (y1 + y2)/2).
        """
        x1, y1, x2, y2 = bbox
        bottom_center = (float((x1 + x2) / 2.0), float(y2))
        centroid = (float((x1 + x2) / 2.0), float((y1 + y2) / 2.0))

        # pointPolygonTest: >= 0 means inside or on contour
        dist_bc = cv2.pointPolygonTest(self.polygon, bottom_center, False)
        dist_c = cv2.pointPolygonTest(self.polygon, centroid, False)
        return dist_bc >= 0 or dist_c >= 0

    def process_track(
        self,
        track_id: int,
        bbox: Tuple[int, int, int, int],
        frame_number: int,
        timestamp_str: str,
        active_track_ids: Optional[Set[int]] = None
    ) -> Dict[str, Any]:
        """
        Process a tracked person for zone intrusion with anti-spam / de-duplication:
        - If person enters restricted zone:
            - If authorized: Tag as AUTHORIZED_ACCESS, do NOT trigger intrusion alarm.
            - If unauthorized:
                - First entry frame: Trigger INTRUSION_NEW alert, capture evidence frame.
                - Subsequent frames while in zone: Keep as INTRUSION_ACTIVE, but DO NOT trigger new alert!
        - If person is outside: status = OUTSIDE_ZONE.
        """
        inside = self.is_inside_zone(bbox)
        is_authorized = (track_id in self.authorized_track_ids)
        personnel_info = self.authorized_personnel_map.get(track_id)

        if track_id not in self.track_states:
            self.track_states[track_id] = {
                "in_zone": False,
                "intrusion_reported": False,
                "first_intrusion_frame": -1,
                "first_intrusion_timestamp": "",
                "is_authorized": is_authorized,
                "personnel_info": personnel_info,
                "frames_in_zone": 0
            }

        state = self.track_states[track_id]
        state["is_authorized"] = is_authorized
        state["personnel_info"] = personnel_info

        event_result = {
            "track_id": track_id,
            "bbox": bbox,
            "is_inside_zone": inside,
            "is_authorized": is_authorized,
            "personnel_info": personnel_info,
            "trigger_new_intrusion": False,
            "display_label": "",
            "color_bgr": (0, 255, 0),  # Default green
            "status": "NORMAL"
        }

        if inside:
            state["frames_in_zone"] += 1

            if is_authorized:
                # Authorized personnel inside restricted zone - DO NOT treat as intruder!
                state["in_zone"] = True
                event_result["status"] = "AUTHORIZED_ACCESS"
                name = personnel_info["name"] if personnel_info else f"Officer #{track_id}"
                event_result["display_label"] = f"AUTHORIZED: {name}"
                event_result["color_bgr"] = (0, 220, 0)  # Solid Bright Green
                event_result["trigger_new_intrusion"] = False

            else:
                # Unauthorized person inside restricted zone!
                event_result["color_bgr"] = (0, 0, 255)  # Bright Red for Intruder

                # Compute bounding box centroid for spatial session continuity
                x1, y1, x2, y2 = bbox
                cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0

                # Match against active spatial sessions within distance threshold and time window
                matched_session = None
                for session in self.active_intrusion_sessions:
                    dt = frame_number - session["last_frame"]
                    if dt <= 75:
                        dist = np.hypot(cx - session["last_centroid"][0], cy - session["last_centroid"][1])
                        max_allowed_dist = 60.0 + dt * 3.5
                        # If session belongs to same track ID, match directly
                        if session["track_id"] == track_id:
                            matched_session = session
                            break
                        # If session belongs to a different track ID: only match if the other track is no longer active in frame (re-ID after occlusion)
                        elif active_track_ids is None or session["track_id"] not in active_track_ids:
                            if dist <= max_allowed_dist:
                                matched_session = session
                                break

                if not state["intrusion_reported"] and matched_session is None:
                    # FIRST TIME ENTRY: Trigger exactly ONE intrusion event
                    state["in_zone"] = True
                    state["intrusion_reported"] = True
                    state["first_intrusion_frame"] = frame_number
                    state["first_intrusion_timestamp"] = timestamp_str

                    # Record new spatial session
                    self.active_intrusion_sessions.append({
                        "session_id": f"SESSION-{track_id}-{frame_number}",
                        "track_id": track_id,
                        "last_centroid": (cx, cy),
                        "last_frame": frame_number,
                        "first_frame": frame_number,
                        "reported": True
                    })

                    event_result["trigger_new_intrusion"] = True
                    event_result["status"] = "INTRUSION_ALERT"
                    event_result["display_label"] = f"INTRUDER ALERT #{track_id}"
                else:
                    # REMAINS IN ZONE OR PERSISTENT SESSION: Maintain intruder tag, NO MULTIPLE INTRUSIONS ENTERTAINED
                    state["in_zone"] = True
                    state["intrusion_reported"] = True
                    if matched_session:
                        matched_session["last_centroid"] = (cx, cy)
                        matched_session["last_frame"] = frame_number
                        matched_session["track_id"] = track_id

                    event_result["trigger_new_intrusion"] = False
                    event_result["status"] = "INTRUSION_ACTIVE"
                    event_result["display_label"] = f"INTRUDER #{track_id} (DWELL: {state['frames_in_zone']}f)"

        else:
            # Person is outside restricted zone
            if state["in_zone"]:
                # Person just exited the zone
                state["in_zone"] = False
                # Note: we retain intrusion_reported so if they stay away or exit, we know past history

            event_result["status"] = "OUTSIDE_ZONE"
            event_result["display_label"] = f"Person #{track_id}"
            event_result["color_bgr"] = (255, 200, 0)  # Cyan/Blue outside zone

        return event_result

    def draw_zone_overlay(self, frame: np.ndarray, active_alert: bool = False) -> np.ndarray:
        """
        Draw the restricted zone polygon on the frame with translucent fill,
        pulsing alert border if an intrusion is actively occurring, and hazard markers.
        """
        overlay = frame.copy()

        # Fill restricted zone with translucent red
        fill_color = (0, 0, 180) if active_alert else (0, 0, 100)
        cv2.fillPoly(overlay, [self.polygon], fill_color)

        # Blend overlay (40% zone color, 60% original image)
        alpha = 0.35
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

        # Draw crisp bright border
        border_color = (0, 0, 255) if active_alert else (0, 140, 255)
        border_thickness = 3 if active_alert else 2
        cv2.polylines(frame, [self.polygon], isClosed=True, color=border_color, thickness=border_thickness)

        # Zone label banner
        label_pos = (self.polygon[0][0], max(self.polygon[0][1] - 10, 30))
        label_text = f"RESTRICTED BORDER ZONE: {self.zone_id}"
        cv2.putText(
            frame,
            label_text,
            label_pos,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 255) if active_alert else (0, 200, 255),
            2
        )

        return frame
