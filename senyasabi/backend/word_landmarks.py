"""Runtime extraction adapted directly from fsl_mediapipe_training.py.

xyz()/frame_to_features() retain the training expressions and feature ordering.
The only addition inside frame_to_features is a lazy MediaPipe import. Do not
import the Colab training script: it installs dependencies, mounts Drive and trains.
"""
from pathlib import Path

import numpy as np

NUM_FRAMES = 24
FEATURE_DIM = 172
POSE_INDICES = [0, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
FEATURE_ORDER = 'pose xyz+visibility, left hand xyz, right hand xyz, presence flags'
NORMALIZATION = 'shoulder midpoint origin and shoulder-width scale'
TASK_ROOT = Path(__file__).resolve().parents[1] / 'resources/models/mediapipe'
HAND_MODEL_PATH = TASK_ROOT / 'hand_landmarker.task'
POSE_MODEL_PATH = TASK_ROOT / 'pose_landmarker_lite.task'


def xyz(lm, cx, cy, scale):
    return [(float(lm.x)-cx)/scale, (float(lm.y)-cy)/scale, float(lm.z)/scale]


def frame_to_features(frame_rgb, hand_detector, pose_detector):
    import mediapipe as mp
    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(frame_rgb))
    pose_result = pose_detector.detect(image)
    hand_result = hand_detector.detect(image)
    pose = pose_result.pose_landmarks[0] if pose_result.pose_landmarks else []
    if len(pose) > 12:
        ls, rs = pose[11], pose[12]
        cx, cy = (float(ls.x)+float(rs.x))/2, (float(ls.y)+float(rs.y))/2
        scale = max(float(np.hypot(float(ls.x)-float(rs.x), float(ls.y)-float(rs.y))), 0.08)
    else:
        cx, cy, scale = 0.5, 0.5, 0.25

    features = []
    for index in POSE_INDICES:
        if len(pose) > index:
            lm = pose[index]
            features.extend(xyz(lm, cx, cy, scale))
            features.append(float(getattr(lm, 'visibility', 1.0) or 0.0))
        else:
            features.extend([0.0]*4)

    hands = {'Left': None, 'Right': None}
    used = set()
    for idx, (landmarks, handedness) in enumerate(zip(hand_result.hand_landmarks, hand_result.handedness)):
        name = handedness[0].category_name if handedness else ''
        if name in hands and hands[name] is None:
            hands[name] = landmarks
            used.add(idx)
    leftovers = [h for i, h in enumerate(hand_result.hand_landmarks) if i not in used]
    for slot, landmarks in zip([k for k,v in hands.items() if v is None], leftovers):
        hands[slot] = landmarks

    presence = []
    for name in ('Left','Right'):
        landmarks = hands[name]
        presence.append(1.0 if landmarks else 0.0)
        if landmarks:
            for lm in landmarks[:21]:
                features.extend(xyz(lm, cx, cy, scale))
        else:
            features.extend([0.0]*(21*3))
    features.extend(presence)
    vector = np.nan_to_num(np.asarray(features, np.float32))
    if vector.shape != (FEATURE_DIM,):
        raise RuntimeError(f'Feature shape {vector.shape}, expected {(FEATURE_DIM,)}')
    return vector, bool(pose), int(sum(presence))


def validate_landmark_config(config):
    """Accept the exported training JSON unchanged; reject incompatible pipelines."""
    expected = {'num_frames': NUM_FRAMES, 'feature_dim': FEATURE_DIM, 'num_hands': 2,
                'pose_indices': POSE_INDICES, 'feature_order': FEATURE_ORDER,
                'normalization': NORMALIZATION}
    if not isinstance(config, dict):
        raise ValueError('landmark_config.json must contain an object.')
    for key, value in expected.items():
        actual = config.get(key)
        if actual != value or (type(value) is int and type(actual) is not int):
            raise ValueError(f'Incompatible landmark_config {key}: expected {value!r}, got {actual!r}.')
    # A scaler would change the verified feature distribution and is not used here.
    if config.get('scaler_path') or config.get('scaler_required'):
        raise ValueError('Category MediaPipe-GRU training uses no scaler.')
    return dict(config)


def make_landmarkers(hand_model_path=HAND_MODEL_PATH, pose_model_path=POSE_MODEL_PATH):
    """Training IMAGE mode/options; deployment resolves assets locally, never downloads."""
    for path in (hand_model_path, pose_model_path):
        if not Path(path).is_file():
            raise FileNotFoundError(f'MediaPipe task asset is not installed: {Path(path).name}')
    import mediapipe as mp
    BaseOptions = mp.tasks.BaseOptions
    RunningMode = mp.tasks.vision.RunningMode
    HandLandmarker = mp.tasks.vision.HandLandmarker
    HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
    PoseLandmarker = mp.tasks.vision.PoseLandmarker
    PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
    hand_options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(hand_model_path)),
        running_mode=RunningMode.IMAGE,
        num_hands=2,
        min_hand_detection_confidence=0.35,
        min_hand_presence_confidence=0.35,
    )
    pose_options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(pose_model_path)),
        running_mode=RunningMode.IMAGE,
        num_poses=1,
        min_pose_detection_confidence=0.35,
        min_pose_presence_confidence=0.35,
    )
    hand = HandLandmarker.create_from_options(hand_options)
    try:
        pose = PoseLandmarker.create_from_options(pose_options)
    except Exception:
        hand.close()
        raise
    return hand, pose




class _LandmarkerWrapper:
    def __init__(self, detector, preprocessor, kind):
        self._detector = detector
        self._preprocessor = preprocessor
        self._kind = kind
        self._last_valid_pose = None

    def detect(self, image):
        res = self._detector.detect(image)
        try:
            if self._kind == 'hand':
                self._preprocessor.last_hand_landmarks = list(res.hand_landmarks) if res and res.hand_landmarks else []
            elif self._kind == 'pose':
                pose_landmarks = res.pose_landmarks[0] if res and res.pose_landmarks else []
                if len(pose_landmarks) > 12:
                    ls, rs = pose_landmarks[11], pose_landmarks[12]
                    ls_vis = getattr(ls, 'visibility', 1.0) or 0.0
                    rs_vis = getattr(rs, 'visibility', 1.0) or 0.0
                    if ls_vis >= 0.40 and rs_vis >= 0.40:
                        self._last_valid_pose = pose_landmarks
                        self._preprocessor.last_pose_landmarks = pose_landmarks
                    elif self._last_valid_pose is not None:
                        from types import SimpleNamespace as NS
                        res = NS(pose_landmarks=[self._last_valid_pose])
                        self._preprocessor.last_pose_landmarks = self._last_valid_pose
                    else:
                        from types import SimpleNamespace as NS
                        res = NS(pose_landmarks=[])
                        self._preprocessor.last_pose_landmarks = []
                elif self._last_valid_pose is not None:
                    from types import SimpleNamespace as NS
                    if not (res and res.pose_landmarks):
                        res = NS(pose_landmarks=[self._last_valid_pose])
                    self._preprocessor.last_pose_landmarks = self._last_valid_pose
                else:
                    self._preprocessor.last_pose_landmarks = pose_landmarks
        except Exception:
            pass
        return res

    def close(self):
        if hasattr(self._detector, 'close'):
            self._detector.close()

    def __getattr__(self, name):
        return getattr(self._detector, name)

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
]
ARM_CONNECTIONS = [(11, 12), (11, 13), (13, 15), (12, 14), (14, 16)]


def draw_landmarks_on_frame(frame_bgr, hand_landmarks_list=None, pose_landmarks=None):
    import cv2
    if frame_bgr is None:
        return None
    annotated = frame_bgr.copy()
    h, w = frame_bgr.shape[:2]

    # Draw arms / shoulders if pose landmarks present
    if pose_landmarks and len(pose_landmarks) > 16:
        pose_pts = {}
        for idx in (11, 12, 13, 14, 15, 16):
            if idx < len(pose_landmarks):
                lm = pose_landmarks[idx]
                vis = getattr(lm, 'visibility', 1.0)
                if vis is None or vis > 0.35:
                    pose_pts[idx] = (int(lm.x * w), int(lm.y * h))
        for p1, p2 in ARM_CONNECTIONS:
            if p1 in pose_pts and p2 in pose_pts:
                cv2.line(annotated, pose_pts[p1], pose_pts[p2], (180, 230, 180), 2, cv2.LINE_AA)
        for pt in pose_pts.values():
            cv2.circle(annotated, pt, 4, (80, 190, 100), -1, cv2.LINE_AA)

    # Draw hands
    if hand_landmarks_list:
        for hand in hand_landmarks_list:
            if not hand:
                continue
            pts = [(int(lm.x * w), int(lm.y * h)) for lm in hand]
            for p1, p2 in HAND_CONNECTIONS:
                if p1 < len(pts) and p2 < len(pts):
                    cv2.line(annotated, pts[p1], pts[p2], (255, 255, 255), 2, cv2.LINE_AA)
            for pt in pts:
                cv2.circle(annotated, pt, 4, (58, 145, 232), -1, cv2.LINE_AA)
                cv2.circle(annotated, pt, 2, (255, 255, 255), -1, cv2.LINE_AA)

    return annotated

class WordLandmarkPreprocessor:
    """Own the two Tasks detectors; every camera frame yields the training vector."""
    def __init__(self, config, hand_model_path=HAND_MODEL_PATH, pose_model_path=POSE_MODEL_PATH):
        self.config = validate_landmark_config(config)
        raw_hand, raw_pose = make_landmarkers(hand_model_path, pose_model_path)
        self.last_hand_landmarks = []
        self.last_pose_landmarks = []
        self.hand_detector = _LandmarkerWrapper(raw_hand, self, 'hand')
        self.pose_detector = _LandmarkerWrapper(raw_pose, self, 'pose')

    def process(self, frame_bgr):
        import cv2
        # Training reads unmirrored RGB frames. Do not flip or swap handedness slots.
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        return frame_to_features(frame_rgb, self.hand_detector, self.pose_detector)

    def draw(self, frame_bgr):
        return draw_landmarks_on_frame(
            frame_bgr,
            hand_landmarks_list=self.last_hand_landmarks,
            pose_landmarks=self.last_pose_landmarks
        )

    def close(self):
        hand, pose = self.hand_detector, self.pose_detector
        self.hand_detector = self.pose_detector = None
        try:
            if hand is not None:
                hand.close()
        finally:
            if pose is not None:
                pose.close()
