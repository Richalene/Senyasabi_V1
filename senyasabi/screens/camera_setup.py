"""Application consent and local camera selection; OS privacy permissions are separate."""
import logging
from pathlib import Path
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                              QComboBox, QStackedWidget, QWidget, QInputDialog, QScrollArea)
from backend.camera_service import CameraDevice, get_camera_service, friendly_camera_error
from screens.camera_preview import RoundedCameraPreview
from screens.loading import LoadingOverlay
from screens.navigation import install_page_menu

log = logging.getLogger(__name__)


class CameraSetupDialog(QDialog):
    def __init__(self, parent=None, *, service=None, onboarding=False):
        super().__init__(parent)
        self.service = service if service is not None else get_camera_service()
        self.setObjectName('cameraSetupDialog')
        self.setWindowTitle('SenyaSabi — Camera Settings')
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.resize(640, 590)
        self.capture = None
        self.tested_id = None
        self.devices = []
        self._closing = False
        self._misses = 0
        self.setStyleSheet((Path(__file__).resolve().parents[1] / 'resources/styles/common.qss').read_text())
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(24, 20, 24, 20)
        title_row = QHBoxLayout()
        title = self.heading('Your camera, your choice')
        title.setMinimumHeight(64)
        title_row.addWidget(title, 1)
        title_row.addSpacing(76)
        self.body.addLayout(title_row)
        self.pages = QStackedWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidget(self.pages)
        self.body.addWidget(scroll, 1)
        consent = QWidget()
        intro = QVBoxLayout(consent)
        text = QLabel('SenyaSabi uses your camera to recognize your signs.\n\n'
                      'The camera starts only for recognition activities. Leaving an activity stops it. '
                      'You can choose a camera now and change it later in Camera Settings.\n\n'
                      'Frames are processed on this device; SenyaSabi does not record or upload them. '
                      'Your operating system may separately ask for camera permission.')
        text.setWordWrap(True)
        text.setProperty('class', 'bodyText')
        intro.addWidget(text, 1)
        setup = QPushButton('Set Up Camera')
        setup.setProperty('class', 'primaryButton')
        setup.clicked.connect(self.show_devices)
        intro.addWidget(setup)
        not_now = QPushButton('Not Now')
        not_now.clicked.connect(self.reject)
        intro.addWidget(not_now)
        self.pages.addWidget(consent)
        self.selection = QWidget()
        choices = QVBoxLayout(self.selection)
        self.status = QLabel('Choose which camera SenyaSabi uses.')
        self.status.setWordWrap(True)
        self.status.setProperty('class', 'bodyText')
        choices.addWidget(self.status)
        self.combo = QComboBox()
        self.combo.setAccessibleName('Camera')
        self.combo.currentIndexChanged.connect(self.selection_changed)
        choices.addWidget(self.combo)
        controls = QHBoxLayout()
        self.test_button = QPushButton('Test Camera')
        self.test_button.setProperty('class', 'primaryButton')
        self.test_button.clicked.connect(self.test_camera)
        self.retry_button = QPushButton('Refresh Cameras')
        self.retry_button.clicked.connect(self.refresh)
        controls.addWidget(self.test_button)
        controls.addWidget(self.retry_button)
        choices.addLayout(controls)
        self.preview = RoundedCameraPreview('Your camera preview will appear here.')
        self.preview.setObjectName('cameraPreview')
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setWordWrap(True)
        self.preview.setMinimumHeight(170)
        choices.addWidget(self.preview, 1)
        self.manual_button = QPushButton('Choose by device number')
        self.manual_button.setProperty('class', 'quietButton')
        self.manual_button.clicked.connect(self.choose_numeric)
        choices.addWidget(self.manual_button)
        self.save_button = QPushButton('Save / Use Camera')
        self.save_button.setProperty('class', 'primaryButton')
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save)
        choices.addWidget(self.save_button)
        self.without_button = QPushButton('Continue Without Camera')
        self.without_button.clicked.connect(self.reject)
        choices.addWidget(self.without_button)
        self.pages.addWidget(self.selection)
        install_page_menu(self)
        self.loading = LoadingOverlay(self)
        self.timer = QTimer(self)
        self.timer.setInterval(40)
        self.timer.timeout.connect(self.read_frame)
        if not onboarding:
            self.show_devices()

    @staticmethod
    def heading(text):
        label = QLabel(text)
        label.setProperty('class', 'pageTitle')
        label.setWordWrap(True)
        return label

    def show_devices(self):
        self.pages.setCurrentWidget(self.selection)
        self.refresh()

    def refresh(self):
        self.stop_preview()
        self.devices = self.service.discover()
        selected = self.service.selected_device()
        if selected and selected.backend == 'opencv' and selected not in self.devices:
            self.devices.append(selected)
        self.combo.blockSignals(True)
        self.combo.clear()
        for device in self.devices:
            self.combo.addItem(device.name, device)
        if selected:
            for index, device in enumerate(self.devices):
                if device.device_id == selected.device_id:
                    self.combo.setCurrentIndex(index)
        self.combo.blockSignals(False)
        self.selection_changed()
        self.status.setText('Choose a camera, then test the preview before saving.' if self.devices else
                            'No camera was found. You can still explore SenyaSabi, but camera-based activities won’t be available. '
                            'Connect a camera and refresh, or continue without one.')

    def selection_changed(self, *args):
        self.stop_preview()
        self.tested_id = None
        self.save_button.setEnabled(False)
        self.test_button.setEnabled(self.combo.currentData() is not None)
        self.preview.clear()
        self.preview.setText('Test the selected camera to see a preview.')

    def choose_numeric(self):
        index, accepted = QInputDialog.getInt(self, 'Camera device number',
            'Use this fallback only if your camera is missing from the list.\nTest the preview to confirm the device.', 0, 0, 15)
        if accepted:
            device = CameraDevice(f'opencv:{index}', f'Camera device {index}', 'opencv', index)
            self.combo.addItem(device.name, device)
            self.combo.setCurrentIndex(self.combo.count()-1)

    def test_camera(self):
        if self.loading.busy:
            return
        self.stop_preview()
        device = self.combo.currentData()
        if device is None:
            return
        self.tested_id = None
        self.save_button.setEnabled(False)
        self.test_button.setEnabled(False)
        self.combo.setEnabled(False)
        self.status.setText('Starting your camera…')
        self.loading.run(lambda: self.service.open_capture(owner=self, device=device),
                         lambda capture: self.preview_ready(capture, device), self.preview_failed,
                         dispose=lambda capture: capture.release(), message='Starting your camera…')

    def preview_ready(self, capture, device):
        self.capture = capture
        self._misses = 0
        self._testing_device = device
        self.test_button.setEnabled(True)
        self.combo.setEnabled(True)
        self.status.setText('Check that the preview shows the camera you want to use.')
        self.timer.start()

    def preview_failed(self, error):
        log.warning('Camera preview unavailable: %s', error)
        self.stop_preview()
        self.combo.setEnabled(True)
        self.test_button.setEnabled(self.combo.currentData() is not None)
        self.save_button.setEnabled(False)
        self.tested_id = None
        self.preview.clear()
        self.preview.setText('Camera preview unavailable')
        self.status.setText(friendly_camera_error(error))

    def read_frame(self):
        try:
            ok, frame = self.capture.read()
            if not ok:
                self._misses += 1
                if self._misses >= 3:
                    self.preview_failed(None)
                return
            self._misses = 0
            self.preview.set_bgr_frame(frame)
            self.tested_id = self._testing_device.device_id
            self.save_button.setEnabled(True)
        except Exception as error:
            log.exception('Camera preview failed')
            self.preview_failed(error)

    def save(self):
        device = self.combo.currentData()
        if device is None or self.tested_id != device.device_id:
            return
        self.stop_preview()
        try:
            self.service.save_selection(device)
        except RuntimeError:
            log.exception('Camera preferences could not be saved')
            self.status.setText('Your camera works, but its settings could not be saved. Please retry.')
            return
        self.accept()

    def stop_preview(self):
        if hasattr(self, 'timer'):
            self.timer.stop()
        if hasattr(self, 'loading'):
            self.loading.cancel()
        capture, self.capture = self.capture, None
        if capture is not None:
            capture.release()

    def done(self, result):
        self._closing = True
        self.stop_preview()
        super().done(result)

    def closeEvent(self, event):
        self.stop_preview()
        super().closeEvent(event)

    def hideEvent(self, event):
        self.stop_preview()
        super().hideEvent(event)
