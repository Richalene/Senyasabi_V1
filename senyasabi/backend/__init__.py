# backend/__init__.py
"""
SenyaSabi backend.

Heavy deps (TensorFlow/MediaPipe/OpenCV) are imported lazily so the API
server and scripts can import backend.* without loading them.
"""
from importlib import import_module
from typing import TYPE_CHECKING

# Import version from parent package
try:
    from .. import __version__
except ImportError:
    __version__ = "1.0.0"

_LAZY = {
    "SignRecognitionEngine": ".recognition_engine",
    "HandLandmarkExtractor": ".recognition_engine",
    "SignPredictor": ".recognition_engine",
    "FrameResult": ".recognition_engine",
    "PredictionResult": ".recognition_engine",
    "LessonContent": ".content_data",
    "CameraPracticeSession": ".session_state",
    "KeyPressSpellingSession": ".session_state",
    "SessionState": ".session_state",
    "Event": ".session_state",
    "initialize_database": ".database.init_db",
    "rebuild_database": ".database.init_db",
    "get_schema_version": ".database.init_db",
}

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
    "get_schema_version"
]

if TYPE_CHECKING:
    from .recognition_engine import SignRecognitionEngine, HandLandmarkExtractor, SignPredictor, FrameResult, PredictionResult 
    from .content_data import LessonContent
    from .session_state import CameraPracticeSession, KeyPressSpellingSession, SessionState, Event
    from .database.init_db import initialize_database, rebuild_database, get_schema_version

def __getattr__(name):
    module = _LAZY.get(name)
    if module is None:
        raise AttributeError(
            f"module {__name__!r} has no attribute {name!r}"
        )
    return getattr(import_module(module, __name__), name)