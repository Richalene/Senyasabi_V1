"""
Hand-landmark extraction + sign prediction + camera capture.

Pure OpenCV / MediaPipe / TensorFlow — no Qt. Feed it frames (or let it own
the camera) and read back plain Python/NumPy results; wire those into
whatever widgets you built in Qt Creator (PySide6).
"""
import json
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf

from . import config


@dataclass
class PredictionResult:
    label: str
    confidence: float


@dataclass
class FrameResult:
    """Everything a UI layer needs to render one camera frame."""
    frame_bgr: np.ndarray            # raw (flipped) camera frame, BGR
    annotated_bgr: np.ndarray        # frame with hand skeleton drawn on it
    hand_detected: bool
    prediction: Optional[PredictionResult]


class HandLandmarkExtractor:
    """Wraps a single MediaPipe Hands instance."""

    def __init__(self, max_num_hands: int = 1,
                 min_detection_confidence: float = 0.5,
                 min_tracking_confidence: float = 0.5):
        self._mp_hands = mp.solutions.hands
        self._mp_drawing = mp.solutions.drawing_utils
        self._hands = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

    def process(self, frame_bgr: np.ndarray):
        """Runs MediaPipe on a BGR frame. Returns (features, mp_result).
        features is a flattened, wrist-centered, palm-scale-normalized
        63-length array, or None if no hand / degenerate scale."""
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        result = self._hands.process(rgb)
        if not result.multi_hand_landmarks:
            return None, result
        lm = result.multi_hand_landmarks[0].landmark
        coords = np.array([[p.x, p.y, p.z] for p in lm])
        coords -= coords[0]                      # translate to wrist origin
        scale = np.linalg.norm(coords[9])         # normalize by palm length
        if scale == 0:
            return None, result
        coords /= scale
        return coords.flatten(), result

    def draw(self, frame_bgr: np.ndarray, mp_result) -> np.ndarray:
        """Returns a copy of frame_bgr with the hand skeleton drawn on it."""
        annotated = frame_bgr.copy()
        if mp_result.multi_hand_landmarks:
            for hand_landmarks in mp_result.multi_hand_landmarks:
                self._mp_drawing.draw_landmarks(
                    annotated, hand_landmarks, self._mp_hands.HAND_CONNECTIONS,
                    self._mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2, circle_radius=3),
                    self._mp_drawing.DrawingSpec(color=(232, 145, 58), thickness=2, circle_radius=2),
                )
        return annotated

    def close(self):
        self._hands.close()


class SignPredictor:
    """Loads one trained Keras model + its label list, and predicts.

    Pass either `labels_path` (a JSON file with a list of class names) or
    `labels_fallback` (a plain Python list, e.g. A-Z) — not both required.
    `scaler_path` is optional; skip it if you don't have a pickled scaler.
    """

    def __init__(self, model_path: Path,
                 labels_path: Optional[Path] = None,
                 labels_fallback: Optional[list] = None,
                 scaler_path: Optional[Path] = None):
        self.model = tf.keras.models.load_model(model_path)

        if labels_path is not None:
            self.class_names = json.loads(Path(labels_path).read_text())
        elif labels_fallback is not None:
            self.class_names = list(labels_fallback)
        else:
            raise ValueError("SignPredictor needs labels_path or labels_fallback")

        self.scaler = None
        if scaler_path is not None:
            self.scaler = pickle.loads(Path(scaler_path).read_bytes())

    def predict(self, features: np.ndarray) -> PredictionResult:
        x = self.scaler.transform([features]) if self.scaler is not None else np.array([features])
        probs = self.model.predict(x, verbose=0)[0]
        idx = int(np.argmax(probs))
        return PredictionResult(self.class_names[idx], float(probs[idx]))


class SignRecognitionEngine:
    """
    High-level facade combining camera + landmark extraction + prediction.

    `mode` picks which model/label-set to load, from config.MODELS
    ("alphabet" or "words"). Switch modes (e.g. Alphabet screen <-> Sign
    Detective screen) with `set_mode()` instead of tearing down the camera.

    Typical PySide6 wiring, in your QMainWindow subclass:

        self.engine = SignRecognitionEngine(mode="alphabet")
        self.engine.open_camera()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_tick)
        self.timer.start(15)

        def on_tick(self):
            result = self.engine.read_frame()
            if result is None:
                return
            qimg = frame_to_qimage(result.annotated_bgr)   # your own helper
            self.ui.cameraLabel.setPixmap(QPixmap.fromImage(qimg))
            if result.prediction:
                self.ui.predLabel.setText(result.prediction.label)
                self.ui.confLabel.setText(f"{result.prediction.confidence:.0%}")

        def closeEvent(self, event):
            self.timer.stop()
            self.engine.close()
            event.accept()
    """

    def __init__(self, mode: str = "alphabet", cam_index: int = config.CAM_INDEX):
        self.cam_index = cam_index
        self.extractor = HandLandmarkExtractor()
        self.mode = mode
        self.predictor = self._build_predictor(mode)
        self._cap: Optional[cv2.VideoCapture] = None

    @staticmethod
    def _build_predictor(mode: str) -> SignPredictor:
        if mode not in config.MODELS:
            raise ValueError(f"Unknown mode {mode!r}, expected one of {list(config.MODELS)}")
        spec = config.MODELS[mode]
        return SignPredictor(
            model_path=spec["model_path"],
            labels_path=spec["labels_path"],
            labels_fallback=spec["labels_fallback"],
            scaler_path=spec["scaler_path"],
        )

    def set_mode(self, mode: str):
        """Swap the loaded model without reopening the camera."""
        if mode == self.mode:
            return
        self.predictor = self._build_predictor(mode)
        self.mode = mode

    def open_camera(self) -> bool:
        self._cap = cv2.VideoCapture(self.cam_index)
        return self._cap.isOpened()

    def close_camera(self):
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def read_frame(self) -> Optional[FrameResult]:
        if self._cap is None:
            raise RuntimeError("Camera not open — call open_camera() first.")
        ok, frame = self._cap.read()
        if not ok:
            return None
        frame = cv2.flip(frame, 1)
        features, mp_result = self.extractor.process(frame)
        annotated = self.extractor.draw(frame, mp_result)
        prediction = self.predictor.predict(features) if features is not None else None
        return FrameResult(
            frame_bgr=frame,
            annotated_bgr=annotated,
            hand_detected=features is not None,
            prediction=prediction,
        )

    def close(self):
        self.close_camera()
        self.extractor.close()