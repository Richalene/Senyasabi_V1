"""
SenyaSabi recognition backend.

Pure Python / OpenCV / MediaPipe / TensorFlow — no Qt.
Import from here in your Qt Creator (PySide6) project and wire the results
into whatever widgets you designed with `main.py` / `ui_form.py`.
"""
from .recognition_engine import (
    SignRecognitionEngine,
    HandLandmarkExtractor,
    SignPredictor,
    FrameResult,
    PredictionResult,
)
from .content_data import LessonContent
from .session_state import (
    CameraPracticeSession,
    KeyPressSpellingSession,
    SessionState,
    Event,
)

__all__ = [
    "SignRecognitionEngine",
    "HandLandmarkExtractor",
    "SignPredictor",
    "FrameResult",
    "PredictionResult",
    "LessonContent",
    "CameraPracticeSession",
    "KeyPressSpellingSession",
    "SessionState",
    "Event",
]
