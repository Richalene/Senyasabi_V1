"""
SenyaSabi recognition backend.

Pure Python / OpenCV / MediaPipe / TensorFlow — no Qt.
Import from here in your Qt Creator (PySide6) project and wire the results
into whatever widgets you designed with `main.py` / `ui/ui_form.py`.
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
from .database import initialize_database, rebuild_database, get_schema_version

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
    "initialize_database",
    "rebuild_database",
    "get_schema_version",
]
