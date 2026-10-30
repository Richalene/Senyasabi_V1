"""Local camera choice and exclusive capture. No recording, upload or DB access."""
from dataclasses import dataclass, field
import logging
from queue import Empty, Full, Queue
from threading import Event, Lock
from time import monotonic

from PySide6.QtCore import QObject, QSettings, QThread, Signal, Slot, Qt
from . import camera_ownership

log = logging.getLogger(__name__)


class CameraError(RuntimeError):
    pass


@dataclass(frozen=True)
class CameraDevice:
    device_id: str
    name: str
    backend: str = 'qt'
    index: int | None = None
    qt_device: object = field(default=None, compare=False, repr=False)


def friendly_camera_error(error=None):
    return ('The camera could not be started. It may be disconnected, in use by another app, '
            'or blocked by your system’s camera privacy settings. Retry or choose another camera.')


class _CameraWorker(QObject):
    stop_requested = Signal()

    def __init__(self, capture, device):
        super().__init__()
        self.capture, self.device = capture, device
        self.camera = self.session = self.sink = None
        self.stop_requested.connect(self.stop)

    @Slot()
    def start(self):
        try:
            from PySide6.QtMultimedia import QCamera, QMediaCaptureSession, QVideoSink
            self.camera = QCamera(self.device, self)
            self.session = QMediaCaptureSession(self)
            self.sink = QVideoSink(self)
            self.session.setCamera(self.camera)
            self.session.setVideoSink(self.sink)
            self.sink.videoFrameChanged.connect(self.frame)
            self.camera.errorOccurred.connect(self.failed)
            self.camera.start()
        except Exception as error:
            log.exception('Camera initialization failed')
            self.capture.error = str(error)
            self.capture.ready.set()
            self.stop()

    def frame(self, frame):
        if self.capture.closed or not frame.isValid():
            return
        try:
            import numpy as np
            from PySide6.QtGui import QImage
            image = frame.toImage().convertToFormat(QImage.Format.Format_RGB888)
            if image.isNull():
                return
            rgb = np.frombuffer(image.constBits(), dtype=np.uint8,
                                count=image.height()*image.bytesPerLine()).reshape(image.height(), image.bytesPerLine())
            # Copy before QImage storage is released; preserve original orientation.
            bgr = rgb[:, :image.width()*3].reshape(image.height(), image.width(), 3)[:, :, ::-1].copy()
            try:
                self.capture.frames.put_nowait(bgr)
            except Full:
                try:
                    self.capture.frames.get_nowait()
                except Empty:
                    pass
                self.capture.frames.put_nowait(bgr)
            self.capture.ready.set()
        except Exception as error:
            log.exception('Camera frame conversion failed')
            self.capture.error = str(error)
            self.capture.ready.set()

    def failed(self, error, message):
        log.warning('Camera device error: %s', message)
        self.capture.error = message
        self.capture.ready.set()

    @Slot()
    def stop(self):
        if self.camera is not None:
            self.camera.stop()
        if self.session is not None:
            self.session.setCamera(None)
            self.session.setVideoSink(None)
        self.thread().quit()


class _QtCapture:
    """OpenCV-shaped BGR reader; the camera's own Qt thread keeps callbacks live."""
    def __init__(self, device):
        self.frames = Queue(maxsize=2)
        self.ready = Event()
        self.error = None
        self.closed = False
        self.thread = QThread()
        self.worker = _CameraWorker(self, device.qt_device)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.start, Qt.ConnectionType.DirectConnection)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.start()
        deadline = monotonic()+8
        while not self.ready.wait(.05):
            if QThread.currentThread().isInterruptionRequested() or monotonic() >= deadline:
                break
        if not self.ready.is_set() or self.error:
            self.error = self.error or 'Timed out waiting for a camera frame.'
            self.release()

    def isOpened(self):
        return not self.closed and not self.error and self.thread.isRunning()

    def read(self):
        if not self.isOpened():
            return False, None
        try:
            return True, self.frames.get(timeout=.15)
        except Empty:
            return False, None

    def release(self):
        if self.closed:
            return
        self.closed = True
        if self.thread.isRunning():
            try:
                self.worker.stop_requested.emit()
            except RuntimeError:
                if self.thread.isRunning():
                    raise
        # Closing is bounded; retain the thread until the OS finishes stopping it.
        self.thread.wait(1500)
        if self.thread.isRunning():
            _STOPPING_CAPTURES.add(self)
            self.thread.finished.connect(lambda: _STOPPING_CAPTURES.discard(self), Qt.ConnectionType.DirectConnection)
            if not self.thread.isRunning():
                _STOPPING_CAPTURES.discard(self)


_STOPPING_CAPTURES = set()


class _OwnedCapture:
    def __init__(self, capture, owner):
        self.capture, self.owner = capture, owner
        self.closed = False
        self.failed_reads = 0
        self.last_frame = monotonic()

    def isOpened(self):
        return not self.closed and self.capture.isOpened()

    def read(self):
        ok, frame = self.capture.read()
        if ok:
            self.failed_reads = 0
            self.last_frame = monotonic()
        else:
            self.failed_reads += 1
            if self.failed_reads >= 3 or monotonic()-self.last_frame > 1.5:
                self.release()
        return ok, frame

    def release(self):
        if self.closed:
            return
        self.closed = True
        try:
            self.capture.release()
        finally:
            if isinstance(self.capture, _QtCapture) and self.capture.thread.isRunning():
                self.capture.thread.finished.connect(lambda: camera_ownership.release(self.owner), Qt.ConnectionType.DirectConnection)
                if not self.capture.thread.isRunning():
                    camera_ownership.release(self.owner)
            else:
                camera_ownership.release(self.owner)


class CameraService:
    def __init__(self, settings=None, device_provider=None, capture_factory=None):
        self.settings = settings if settings is not None else QSettings('SenyaSabi', 'SenyaSabi')
        self.device_provider = device_provider
        self.capture_factory = capture_factory
        self.discovery_error = None
        self._lock = Lock()

    def discover(self):
        try:
            if self.device_provider is not None:
                devices = list(self.device_provider())
            else:
                from PySide6.QtMultimedia import QMediaDevices
                devices = [CameraDevice(bytes(device.id()).hex(), device.description(), qt_device=device)
                           for device in QMediaDevices.videoInputs()]
            self.discovery_error = None
            return devices
        except (ImportError, RuntimeError) as error:
            log.warning('Camera discovery unavailable: %s', error)
            self.discovery_error = str(error)
            return []

    @property
    def configured(self):
        with self._lock:
            return bool(self.settings.value('camera/consented', False, type=bool)
                        and self.settings.value('camera/device_id', ''))

    def selected_device(self):
        with self._lock:
            device_id = self.settings.value('camera/device_id', '')
            if not self.settings.value('camera/consented', False, type=bool) or not device_id:
                return None
            if self.settings.value('camera/backend', 'qt') == 'opencv':
                index = self.settings.value('camera/index', 0, type=int)
                return CameraDevice(device_id, self.settings.value('camera/name', f'Camera {index}'), 'opencv', index)
        # Match the stable identifier, never a guessed Qt-list-to-OpenCV index.
        return next((device for device in self.discover() if device.device_id == device_id), None)

    def save_selection(self, device):
        with self._lock:
            for key, value in {'consented': True, 'device_id': device.device_id,
                               'name': device.name, 'backend': device.backend,
                               'index': device.index if device.index is not None else -1}.items():
                self.settings.setValue(f'camera/{key}', value)
            self.settings.sync()
            if self.settings.status() != QSettings.Status.NoError:
                raise CameraError('Camera preferences could not be saved on this device.')

    def open_capture(self, *, owner, device=None):
        if QThread.currentThread().isInterruptionRequested():
            raise CameraError('Camera initialization was cancelled.')
        device = device or self.selected_device()
        if device is None:
            raise CameraError('Set up a camera before starting recognition.')
        if not camera_ownership.claim(owner):
            raise CameraError('Another SenyaSabi activity is still using the camera. Please retry.')
        capture = None
        owned = None
        try:
            if self.capture_factory is not None:
                capture = self.capture_factory(device)
            elif device.backend == 'qt':
                capture = _QtCapture(device)
            else:
                import cv2
                capture = cv2.VideoCapture(device.index)
            owned = _OwnedCapture(capture, owner)
            if not owned.isOpened():
                raise CameraError(getattr(capture, 'error', None) or 'The selected camera could not be opened.')
            return owned
        except Exception:
            if owned is not None:
                owned.release()
            else:
                try:
                    if capture is not None:
                        capture.release()
                finally:
                    camera_ownership.release(owner)
            raise


_service = None


def get_camera_service():
    global _service
    if _service is None:
        _service = CameraService()
    return _service


def open_selected_capture(owner):
    return get_camera_service().open_capture(owner=owner)
