"""Shared consent gate and camera states for lesson screens."""
import logging
from typing import Optional, Callable, Any
from PySide6.QtCore import Qt, QThread
from PySide6.QtWidgets import QDialog, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel
from backend.camera_service import get_camera_service, friendly_camera_error
from screens.camera_setup import CameraSetupDialog
from screens.loading import LoadingOverlay

log = logging.getLogger(__name__)


def request_camera(parent, ready, cancelled, *, force=False):
    service = get_camera_service()
    if not force and service.selected_device() is not None:
        ready()
        return None
    dialog = CameraSetupDialog(parent, service=service, onboarding=not service.configured)
    dialog.finished.connect(lambda result: ready() if result == QDialog.DialogCode.Accepted else cancelled())
    dialog.finished.connect(dialog.deleteLater)
    dialog.open()
    return dialog


def alphabet_engine():
    from backend.recognition_engine import SignRecognitionEngine
    return SignRecognitionEngine(mode='alphabet')


class CameraActions(QWidget):
    def __init__(self, parent, retry, choose):
        super().__init__(parent)
        self.setObjectName('cameraActions')
        row = QHBoxLayout(self)
        row.setContentsMargins(6, 4, 6, 4)
        for text, action in (('Retry', retry), ('Choose Camera', choose)):
            button = QPushButton(text)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(action)
            row.addWidget(button)
        layout = parent.layout() or QVBoxLayout(parent)
        layout.addStretch()
        layout.addWidget(self)
        self.hide()


class LessonCameraMixin:
    """Mixin class for lesson screens. 
    Expects host classes to define or expose UI elements like _camera_lbl, _session, _timer, etc.
    """
    # Type hints to keep static type checkers happy and eliminate 'unknown attribute' errors
    _camera_lbl: QLabel
    _session: Any
    _timer: Any
    _feedback_timer: Any
    _feedback_action: Any
    _resources_closed: bool
    _engine: Any
    _engine_factory: Callable[[], Any]
    _availability: Optional[Callable[[], Any]]
    _camera_dialog: Optional[QDialog]
    _camera_misses: int
    loading: LoadingOverlay
    camera_actions: CameraActions
    layout_comp: Any
    camDot: QWidget

    def _init_camera(self, factory, availability=None):
        self._engine_factory = factory
        self._availability = availability
        self._camera_dialog = None
        self._camera_misses = 0
        self._resources_closed = False
        self._engine = None
        self.loading = LoadingOverlay(self)
        
        camera_lbl = getattr(self, "_camera_lbl", None)
        if camera_lbl:
            self.camera_actions = CameraActions(camera_lbl, self.start_camera, self.choose_camera)

    def showEvent(self, event):
        # Type-checkers know QWidget has showEvent
        super().showEvent(event) # type: ignore
        
        resources_closed = getattr(self, "_resources_closed", True)
        engine = getattr(self, "_engine", None)
        if not resources_closed and engine is None and not self.loading.busy:
            self.start_camera()

    def start_camera(self, checked=False, *, force=False):
        if self.loading.busy or (self._camera_dialog is not None and self._camera_dialog.isVisible()):
            return
        
        session = getattr(self, "_session", None)
        if session and session.is_done():
            return
            
        if hasattr(self, "_timer") and self._timer:
            self._timer.stop()
        if hasattr(self, "_feedback_timer") and self._feedback_timer:
            self._feedback_timer.stop()
            
        self._feedback_action = None
        self._resources_closed = False
        
        if session and hasattr(session, "reset_waiting"):
            session.reset_waiting()

        stop_worker = getattr(self, '_stop_inference', None)
        worker_gone = stop_worker() if stop_worker else True
        
        engine, self._engine = getattr(self, "_engine", None), None
        if engine is not None and worker_gone:  # else the worker closes it when it exits
            engine.close()
            
        if self._availability is not None and not force:
            state = self._availability()
            if not state.available:
                self._camera_failed(RuntimeError(state.message))
                return
                
        if hasattr(self, "_camera_lbl") and self._camera_lbl:
            self._camera_lbl.clear()
            self._camera_lbl.setText('Set up your camera to practice signs.')
            
        self._camera_dialog = request_camera(self, self._prepare_camera, self._camera_off, force=force)

    def choose_camera(self, checked=False):
        self.start_camera(force=True)

    def _prepare_camera(self):
        self._camera_dialog = None
        if hasattr(self, 'camera_actions') and self.camera_actions is not None:
            self.camera_actions.hide()
            
        if hasattr(self, "_camera_lbl") and self._camera_lbl:
            self._camera_lbl.setText('Preparing your camera…')

        def prepare():
            engine = self._engine_factory()
            try:
                if QThread.currentThread().isInterruptionRequested():
                    raise RuntimeError('Camera initialization cancelled')
                if not engine.open_camera():
                    raise RuntimeError('Camera unavailable')
                return engine
            except Exception:
                engine.close()
                raise
                
        self.loading.run(prepare, self._camera_ready, self._camera_failed,
                         dispose=lambda engine: engine.close(), message='Preparing sign recognition…')

    def _set_cam_dot(self, active: bool):
        if hasattr(self, "layout_comp") and hasattr(self.layout_comp, "set_camera_active"):
            self.layout_comp.set_camera_active(active)
        elif hasattr(self, "camDot") and self.camDot:
            color = "#4ade80" if active else "#ef4444"
            self.camDot.setStyleSheet(f"background-color: {color}; border-radius: 6px;")

    def _camera_ready(self, engine):
        self._engine = engine
        self._camera_misses = 0
        self._set_cam_dot(True)
        if hasattr(self, 'camera_actions') and self.camera_actions is not None:
            self.camera_actions.hide()
            
        if hasattr(self, "_timer") and self._timer:
            self._timer.start()

    def _camera_off(self):
        self._camera_dialog = None
        if hasattr(self, "_camera_lbl") and self._camera_lbl:
            self._camera_lbl.clear()
            self._camera_lbl.setWordWrap(True)
            self._camera_lbl.setText('Camera is off. You can set it up later or use Back to keep exploring.')
            
        self._set_cam_dot(False)
        if hasattr(self, 'camera_actions') and self.camera_actions is not None:
            self.camera_actions.show()

    def _camera_failed(self, error):
        log.warning('Lesson recognition unavailable: %s', error)
        text = str(error).lower()
        if 'not installed' in text or 'missing' in text and ('model' in text or '.task' in text):
            message = 'Recognition model not installed for this module yet. You can browse the lesson or use Back.'
        else:
            message = friendly_camera_error(error)
            
        if hasattr(self, "_camera_lbl") and self._camera_lbl:
            self._camera_lbl.clear()
            self._camera_lbl.setWordWrap(True)
            self._camera_lbl.setText(message)
            
        pred_lbl = getattr(self, '_pred_lbl', None)
        if pred_lbl is not None:
            pred_lbl.setText('Recognition unavailable')
            
        self._set_cam_dot(False)
        if hasattr(self, 'camera_actions') and self.camera_actions is not None:
            self.camera_actions.show()

    def _cancel_camera_setup(self):
        dialog, self._camera_dialog = self._camera_dialog, None
        if dialog is not None:
            dialog.reject()