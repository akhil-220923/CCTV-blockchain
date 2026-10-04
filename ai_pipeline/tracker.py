import numpy as np
from scipy.optimize import linear_sum_assignment
from typing import List, Tuple, Dict, Any, Optional


class KalmanFilterBbox:
    """
    Standard Kalman filter for bounding box tracking in image space:
    State vector: [x, y, a, h, vx, vy, va, vh]
    where (x, y) is center, a is aspect ratio (w/h), h is height.
    """

    def __init__(self):
        ndim, dt = 4, 1.0

        # Motion model state transition
        self._motion_mat = np.eye(2 * ndim, 2 * ndim)
        for i in range(ndim):
            self._motion_mat[i, ndim + i] = dt

        # Measurement matrix (observing x, y, a, h)
        self._update_mat = np.eye(ndim, 2 * ndim)

        # Standard deviations
        self._std_weight_position = 1.0 / 20
        self._std_weight_velocity = 1.0 / 160

    def initiate(self, measurement: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        mean_pos = measurement
        mean_vel = np.zeros_like(mean_pos)
        mean = np.r_[mean_pos, mean_vel]

        std = [
            2 * self._std_weight_position * measurement[3],
            2 * self._std_weight_position * measurement[3],
            1e-2,
            2 * self._std_weight_position * measurement[3],
            10 * self._std_weight_velocity * measurement[3],
            10 * self._std_weight_velocity * measurement[3],
            1e-5,
            10 * self._std_weight_velocity * measurement[3],
        ]
        covariance = np.diag(np.square(std))
        return mean, covariance

    def predict(self, mean: np.ndarray, covariance: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        std_pos = [
            self._std_weight_position * mean[3],
            self._std_weight_position * mean[3],
            1e-2,
            self._std_weight_position * mean[3],
        ]
        std_vel = [
            self._std_weight_velocity * mean[3],
            self._std_weight_velocity * mean[3],
            1e-5,
            self._std_weight_velocity * mean[3],
        ]
        motion_cov = np.diag(np.square(np.r_[std_pos, std_vel]))

        mean = np.dot(self._motion_mat, mean)
        covariance = np.linalg.multi_dot((self._motion_mat, covariance, self._motion_mat.T)) + motion_cov
        return mean, covariance

    def project(self, mean: np.ndarray, covariance: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        std = [
            self._std_weight_position * mean[3],
            self._std_weight_position * mean[3],
            1e-1,
            self._std_weight_position * mean[3],
        ]
        innovation_cov = np.diag(np.square(std))

        mean = np.dot(self._update_mat, mean)
        covariance = np.linalg.multi_dot((self._update_mat, covariance, self._update_mat.T)) + innovation_cov
        return mean, covariance

    def update(self, mean: np.ndarray, covariance: np.ndarray, measurement: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        projected_mean, projected_cov = self.project(mean, covariance)

        chol_factor, lower = np.linalg.cholesky(projected_cov), True
        kalman_gain = np.linalg.lstsq(projected_cov.T, np.dot(covariance, self._update_mat.T).T, rcond=None)[0].T
        innovation = measurement - projected_mean

        new_mean = mean + np.dot(innovation, kalman_gain.T)
        new_covariance = covariance - np.linalg.multi_dot((kalman_gain, projected_cov, kalman_gain.T))
        return new_mean, new_covariance


def bbox_xyxy_to_xyah(bbox: np.ndarray) -> np.ndarray:
    """Convert [x1, y1, x2, y2] to [center_x, center_y, aspect_ratio (w/h), height]."""
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = bbox[0] + w / 2.0
    y = bbox[1] + h / 2.0
    a = w / float(h) if h > 0 else 1.0
    return np.array([x, y, a, h])


def bbox_xyah_to_xyxy(xyah: np.ndarray) -> np.ndarray:
    """Convert [center_x, center_y, aspect_ratio, height] to [x1, y1, x2, y2]."""
    w = xyah[2] * xyah[3]
    h = xyah[3]
    x1 = xyah[0] - w / 2.0
    y1 = xyah[1] - h / 2.0
    x2 = xyah[0] + w / 2.0
    y2 = xyah[1] + h / 2.0
    return np.array([x1, y1, x2, y2])


def calculate_iou_matrix(boxes_a: np.ndarray, boxes_b: np.ndarray) -> np.ndarray:
    """Compute IoU matrix between two sets of bounding boxes [x1, y1, x2, y2]."""
    if len(boxes_a) == 0 or len(boxes_b) == 0:
        return np.zeros((len(boxes_a), len(boxes_b)))

    x11, y11, x12, y12 = np.split(boxes_a, 4, axis=1)
    x21, y21, x22, y22 = np.split(boxes_b, 4, axis=1)

    xA = np.maximum(x11, np.transpose(x21))
    yA = np.maximum(y11, np.transpose(y21))
    xB = np.minimum(x12, np.transpose(x22))
    yB = np.minimum(y12, np.transpose(y22))

    inter_area = np.maximum(0, xB - xA) * np.maximum(0, yB - yA)
    box_a_area = (x12 - x11) * (y12 - y11)
    box_b_area = (x22 - x21) * (y22 - y21)

    union_area = box_a_area + np.transpose(box_b_area) - inter_area
    iou = inter_area / np.maximum(union_area, 1e-6)
    return iou


class TrackState:
    New = 0
    Tracked = 1
    Lost = 2
    Removed = 3


class STrack:
    """Single Track object for ByteTrack."""

    _count = 0

    def __init__(self, tlbr: np.ndarray, score: float, class_id: int = 0):
        self.tlbr = np.asarray(tlbr, dtype=float)
        self.score = float(score)
        self.class_id = int(class_id)
        self.kalman_filter = KalmanFilterBbox()
        self.mean, self.covariance = self.kalman_filter.initiate(bbox_xyxy_to_xyah(self.tlbr))

        self.track_id = 0
        self.is_activated = False
        self.state = TrackState.New
        self.frame_id = 0
        self.tracklet_len = 0

    @classmethod
    def next_id(cls) -> int:
        cls._count += 1
        return cls._count

    @classmethod
    def reset_id(cls):
        cls._count = 0

    def predict(self):
        mean_state = self.mean.copy()
        if self.state != TrackState.Tracked:
            mean_state[7] = 0
        self.mean, self.covariance = self.kalman_filter.predict(mean_state, self.covariance)
        self.tlbr = bbox_xyah_to_xyxy(self.mean[:4])

    def activate(self, frame_id: int):
        self.track_id = self.next_id()
        self.state = TrackState.Tracked
        self.is_activated = True
        self.frame_id = frame_id
        self.tracklet_len = 1

    def re_activate(self, new_track: "STrack", frame_id: int, new_id: bool = False):
        self.mean, self.covariance = self.kalman_filter.update(
            self.mean, self.covariance, bbox_xyxy_to_xyah(new_track.tlbr)
        )
        self.tlbr = bbox_xyah_to_xyxy(self.mean[:4])
        self.tracklet_len += 1
        self.state = TrackState.Tracked
        self.is_activated = True
        self.frame_id = frame_id
        self.score = new_track.score
        if new_id:
            self.track_id = self.next_id()

    def update(self, new_track: "STrack", frame_id: int):
        self.frame_id = frame_id
        self.tracklet_len += 1
        self.mean, self.covariance = self.kalman_filter.update(
            self.mean, self.covariance, bbox_xyxy_to_xyah(new_track.tlbr)
        )
        self.tlbr = bbox_xyah_to_xyxy(self.mean[:4])
        self.state = TrackState.Tracked
        self.is_activated = True
        self.score = new_track.score

    def mark_lost(self):
        self.state = TrackState.Lost

    def mark_removed(self):
        self.state = TrackState.Removed


class ByteTracker:
    """
    ByteTrack implementation:
    Associates high-confidence detections first, then low-confidence detections
    to preserve tracks across occlusions and motion blur.
    """

    def __init__(self, track_thresh: float = 0.45, high_thresh: float = 0.6, match_thresh: float = 0.8, max_time_lost: int = 30):
        self.track_thresh = track_thresh
        self.high_thresh = high_thresh
        self.match_thresh = match_thresh
        self.max_time_lost = max_time_lost
        self.frame_id = 0

        self.tracked_stracks: List[STrack] = []
        self.lost_stracks: List[STrack] = []
        self.removed_stracks: List[STrack] = []
        STrack.reset_id()

    def update(self, detections: List[Dict[str, Any]]) -> List[STrack]:
        """
        detections: list of dicts with 'bbox': [x1, y1, x2, y2], 'confidence': score, 'class': name
        Returns: list of active STrack objects.
        """
        self.frame_id += 1
        activated_stracks = []
        refind_stracks = []
        lost_stracks = []
        removed_stracks = []

        # Split into high and low confidence detections
        dets_first = []
        dets_second = []
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            score = det["confidence"]
            strack = STrack(np.array([x1, y1, x2, y2]), score)
            if score >= self.high_thresh:
                dets_first.append(strack)
            elif score >= self.track_thresh:
                dets_second.append(strack)

        # Predict Kalman states
        unconfirmed = []
        tracked_stracks = []
        for track in self.tracked_stracks:
            if not track.is_activated:
                unconfirmed.append(track)
            else:
                tracked_stracks.append(track)

        strack_pool = tracked_stracks + self.lost_stracks
        for strack in strack_pool:
            strack.predict()

        # --- First Association: Track pool with high-score detections ---
        matched_a, unmatched_tracks_a, unmatched_dets_a = self._match(strack_pool, dets_first, self.match_thresh)

        for itracked, idet in matched_a:
            track = strack_pool[itracked]
            det = dets_first[idet]
            if track.state == TrackState.Tracked:
                track.update(det, self.frame_id)
                activated_stracks.append(track)
            else:
                track.re_activate(det, self.frame_id, new_id=False)
                refind_stracks.append(track)

        # --- Second Association: Remaining tracks with low-score detections ---
        r_tracked_stracks = [strack_pool[i] for i in unmatched_tracks_a if strack_pool[i].state == TrackState.Tracked]
        matched_b, unmatched_tracks_b, _ = self._match(r_tracked_stracks, dets_second, 0.5)

        for itracked, idet in matched_b:
            track = r_tracked_stracks[itracked]
            det = dets_second[idet]
            if track.state == TrackState.Tracked:
                track.update(det, self.frame_id)
                activated_stracks.append(track)
            else:
                track.re_activate(det, self.frame_id, new_id=False)
                refind_stracks.append(track)

        for itracked in unmatched_tracks_b:
            track = r_tracked_stracks[itracked]
            if track.state != TrackState.Lost:
                track.mark_lost()
                lost_stracks.append(track)

        # --- Third: Handle unconfirmed tracks ---
        unmatched_dets = [dets_first[i] for i in unmatched_dets_a]
        matched_c, unmatched_unconfirmed, unmatched_dets_c = self._match(unconfirmed, unmatched_dets, 0.7)

        for itracked, idet in matched_c:
            unconfirmed[itracked].update(unmatched_dets[idet], self.frame_id)
            activated_stracks.append(unconfirmed[itracked])

        for itracked in unmatched_unconfirmed:
            track = unconfirmed[itracked]
            track.mark_removed()
            removed_stracks.append(track)

        # Initialize new tracks for unmatched high-score detections
        for idet in unmatched_dets_c:
            track = unmatched_dets[idet]
            if track.score >= self.high_thresh:
                track.activate(self.frame_id)
                activated_stracks.append(track)

        # Update lost tracks lifecycle
        for track in self.lost_stracks:
            if self.frame_id - track.frame_id > self.max_time_lost:
                track.mark_removed()
                removed_stracks.append(track)

        # Filter tracked stracks
        self.tracked_stracks = [t for t in self.tracked_stracks if t.state == TrackState.Tracked]
        self.tracked_stracks = self._merge_tracks(self.tracked_stracks, activated_stracks)
        self.tracked_stracks = self._merge_tracks(self.tracked_stracks, refind_stracks)

        self.lost_stracks = [t for t in self.lost_stracks if t.state == TrackState.Lost]
        self.lost_stracks = self._merge_tracks(self.lost_stracks, lost_stracks)
        self.lost_stracks = [t for t in self.lost_stracks if t not in self.tracked_stracks]

        self.removed_stracks.extend(removed_stracks)

        # Return active tracks
        output_stracks = [track for track in self.tracked_stracks if track.is_activated]
        return output_stracks

    def _match(self, tracks: List[STrack], dets: List[STrack], threshold: float):
        if len(tracks) == 0 or len(dets) == 0:
            return [], list(range(len(tracks))), list(range(len(dets)))

        boxes_tracks = np.array([t.tlbr for t in tracks])
        boxes_dets = np.array([d.tlbr for d in dets])
        iou_mat = calculate_iou_matrix(boxes_tracks, boxes_dets)
        cost_mat = 1.0 - iou_mat

        row_ind, col_ind = linear_sum_assignment(cost_mat)
        matched = []
        unmatched_tracks = set(range(len(tracks)))
        unmatched_dets = set(range(len(dets)))

        for r, c in zip(row_ind, col_ind):
            if cost_mat[r, c] <= (1.0 - (1.0 - threshold)):
                matched.append((r, c))
                unmatched_tracks.discard(r)
                unmatched_dets.discard(c)

        return matched, list(unmatched_tracks), list(unmatched_dets)

    def _merge_tracks(self, list_a: List[STrack], list_b: List[STrack]) -> List[STrack]:
        track_map = {t.track_id: t for t in list_a}
        for t in list_b:
            track_map[t.track_id] = t
        return list(track_map.values())
