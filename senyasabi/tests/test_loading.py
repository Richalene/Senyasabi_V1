"""Exercise real Qt loading transitions with controlled background operations."""
import os
from pathlib import Path
import sys
from threading import Event
import unittest
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QCoreApplication, QEvent, QObject, QThread, QTimer, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget
from shiboken6 import isValid
from screens.loading import LoadingOverlay, _JOBS
from screens.startup import FittedForm


def wait_for(predicate, timeout=3000):
    for _ in range(max(1, timeout // 10)):
        QApplication.processEvents()
        if predicate():
            return
        QTest.qWait(10)
    raise AssertionError("Timed out waiting for loading transition")


class ShowRecorder(QObject):
    def __init__(self, widget):
        super().__init__(widget)
        self.shows = 0
        widget.installEventFilter(self)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Show:
            self.shows += 1
        return False


class KeyRecorder(QObject):
    def __init__(self, widget):
        super().__init__(widget)
        self.keys = []
        widget.installEventFilter(self)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.KeyPress:
            self.keys.append(event.key())
        return False


class LoadingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def setUp(self):
        self.gates = []
        self.host = QWidget()
        self.host.resize(900, 600)
        layout = QVBoxLayout(self.host)
        self.submit = QPushButton("Submit")
        self.initially_disabled = QPushButton("Unavailable")
        self.initially_disabled.setEnabled(False)
        layout.addWidget(self.submit)
        layout.addWidget(self.initially_disabled)
        self.overlay = LoadingOverlay(self.host)
        self.host.show()
        self.app.processEvents()

    def tearDown(self):
        for gate in self.gates:
            gate.set()
        if isValid(self.host):
            self.host.close()
        wait_for(lambda: not _JOBS)
        if isValid(self.host):
            self.host.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()

    def blocked_operation(self, result=None, error=None):
        gate, started = Event(), Event()
        self.gates.append(gate)

        def operation():
            started.set()
            if not gate.wait(5):
                raise TimeoutError("Test worker was not released")
            if error is not None:
                raise error
            return result

        return operation, gate, started

    def test_slow_work_is_off_thread_and_keeps_qt_responsive(self):
        worker_threads = []
        operation, gate, started = self.blocked_operation("ready")
        success = Mock()

        def record_operation():
            worker_threads.append(QThread.currentThread())
            return operation()

        self.assertTrue(self.overlay.run(record_operation, success, self.fail,
                                        message="Signing you in…", show_delay_ms=10))
        self.assertTrue(self.overlay.busy)
        self.assertEqual(self.overlay.text.text(), "Signing you in…")
        ticks = []
        timer = QTimer(self.host)
        timer.setInterval(5)
        timer.timeout.connect(lambda: ticks.append(True))
        timer.start()
        wait_for(lambda: started.is_set() and len(ticks) >= 3 and self.overlay.isVisible())
        self.assertNotEqual(worker_threads[0], self.app.thread())
        self.assertTrue(self.overlay.busy)
        success.assert_not_called()
        gate.set()
        wait_for(lambda: success.called and not self.overlay.busy)
        success.assert_called_once_with("ready")
        self.assertFalse(self.overlay.isVisible())

    def test_fast_work_does_not_flash_or_wait_for_presentation_delay(self):
        recorder = ShowRecorder(self.overlay)
        success = Mock()
        self.assertTrue(self.overlay.run(lambda: "ready", success, self.fail,
                                        show_delay_ms=1000))
        wait_for(lambda: success.called and not self.overlay.busy, timeout=500)
        self.assertFalse(self.overlay.isVisible())
        self.assertEqual(recorder.shows, 0)
        self.assertFalse(self.overlay.delay.isActive())
        success.assert_called_once_with("ready")

    def test_controls_restore_before_ui_thread_success_callback(self):
        operation, gate, started = self.blocked_operation("ready")
        observed = []

        def success(result):
            observed.append((result, QThread.currentThread(), self.submit.isEnabled(),
                             self.initially_disabled.isEnabled(), self.overlay.busy))

        self.overlay.run(operation, success, self.fail,
                         controls=(self.submit, self.initially_disabled))
        self.assertFalse(self.submit.isEnabled())
        self.assertFalse(self.initially_disabled.isEnabled())
        wait_for(started.is_set)
        gate.set()
        wait_for(lambda: bool(observed))
        self.assertEqual(observed, [("ready", self.app.thread(), True, False, False)])

    def test_error_restores_controls_and_allows_retry_on_ui_thread(self):
        error = RuntimeError("Network unavailable")
        operation, gate, started = self.blocked_operation(error=error)
        observed = []

        def failed(received):
            observed.append((received, QThread.currentThread(), self.submit.isEnabled(),
                             self.overlay.busy))

        self.overlay.run(operation, self.fail, failed, controls=(self.submit,))
        wait_for(started.is_set)
        gate.set()
        wait_for(lambda: bool(observed))
        self.assertEqual(observed, [(error, self.app.thread(), True, False)])
        success = Mock()
        self.assertTrue(self.overlay.run(lambda: "retried", success, self.fail,
                                        controls=(self.submit,)))
        wait_for(lambda: success.called)
        success.assert_called_once_with("retried")
        self.assertTrue(self.submit.isEnabled())

    def test_duplicate_run_is_rejected_without_replacing_operation(self):
        operation, gate, started = self.blocked_operation("first")
        success, duplicate, duplicate_success = Mock(), Mock(), Mock()
        self.assertTrue(self.overlay.run(operation, success, self.fail,
                                        message="First operation", controls=(self.submit,)))
        wait_for(started.is_set)
        self.assertFalse(self.overlay.run(duplicate, duplicate_success, self.fail,
                                         message="Second operation"))
        self.assertEqual(self.overlay.text.text(), "First operation")
        self.assertFalse(self.submit.isEnabled())
        gate.set()
        wait_for(lambda: success.called)
        success.assert_called_once_with("first")
        duplicate.assert_not_called()
        duplicate_success.assert_not_called()
        self.assertTrue(self.submit.isEnabled())

    def test_cancel_disposes_late_result_once_and_restores_controls(self):
        result = object()
        operation, gate, started = self.blocked_operation(result)
        success, failure, dispose = Mock(), Mock(), Mock()
        self.overlay.run(operation, success, failure, dispose,
                         controls=(self.submit, self.initially_disabled), show_delay_ms=0)
        wait_for(lambda: started.is_set() and self.overlay.isVisible())
        self.overlay.cancel()
        self.overlay.cancel()
        self.assertFalse(self.overlay.busy)
        self.assertFalse(self.overlay.isVisible())
        self.assertTrue(self.submit.isEnabled())
        self.assertFalse(self.initially_disabled.isEnabled())
        gate.set()
        wait_for(lambda: not _JOBS)
        dispose.assert_called_once_with(result)
        success.assert_not_called()
        failure.assert_not_called()

    def test_hiding_parent_cancels_pending_work(self):
        operation, gate, started = self.blocked_operation(object())
        success, failure, dispose = Mock(), Mock(), Mock()
        self.overlay.run(operation, success, failure, dispose, controls=(self.submit,))
        wait_for(started.is_set)
        self.host.hide()
        self.assertFalse(self.overlay.busy)
        self.assertTrue(self.submit.isEnabled())
        gate.set()
        wait_for(lambda: not _JOBS)
        dispose.assert_called_once()
        success.assert_not_called()
        failure.assert_not_called()

    def test_late_error_after_navigation_does_not_reopen_error_ui(self):
        operation, gate, started = self.blocked_operation(error=RuntimeError("Disconnected"))
        success, failure = Mock(), Mock()
        self.overlay.run(operation, success, failure)
        wait_for(started.is_set)
        self.host.hide()
        gate.set()
        wait_for(lambda: not _JOBS)
        success.assert_not_called()
        failure.assert_not_called()

    def test_deleting_parent_suppresses_callbacks_and_disposes_late_result(self):
        result = object()
        operation, gate, started = self.blocked_operation(result)
        success, failure, dispose = Mock(), Mock(), Mock()
        self.overlay.run(operation, success, failure, dispose, controls=(self.submit,))
        wait_for(started.is_set)
        self.host.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.assertFalse(isValid(self.host))
        gate.set()
        wait_for(lambda: not _JOBS)
        dispose.assert_called_once_with(result)
        success.assert_not_called()
        failure.assert_not_called()

    def test_cancelled_old_result_cannot_finish_replacement_operation(self):
        operation, gate, started = self.blocked_operation("old")
        old_success, old_failure, old_dispose = Mock(), Mock(), Mock()
        self.overlay.run(operation, old_success, old_failure, old_dispose,
                         controls=(self.submit,))
        wait_for(started.is_set)
        self.overlay.cancel()
        replacement, replacement_gate, replacement_started = self.blocked_operation("new")
        success = Mock()
        self.assertTrue(self.overlay.run(replacement, success, self.fail,
                                        controls=(self.submit,)))
        wait_for(replacement_started.is_set)
        gate.set()
        wait_for(lambda: old_dispose.called)
        self.assertTrue(self.overlay.busy)
        self.assertFalse(self.submit.isEnabled())
        success.assert_not_called()
        old_success.assert_not_called()
        old_failure.assert_not_called()
        old_dispose.assert_called_once_with("old")
        replacement_gate.set()
        wait_for(lambda: success.called)
        success.assert_called_once_with("new")
        self.assertTrue(self.submit.isEnabled())

    def test_overlay_tracks_resize_fullscreen_and_fitted_form(self):
        operation, gate, started = self.blocked_operation("ready")
        success = Mock()
        self.host._fitted_form = FittedForm(self.host)
        self.overlay.run(operation, success, self.fail, show_delay_ms=0)
        wait_for(lambda: started.is_set() and self.overlay.isVisible())
        for width, height in ((640, 480), (1280, 720), (1024, 900)):
            self.host.resize(width, height)
            self.host._fitted_form.fit()
            self.app.processEvents()
            self.assertEqual(self.overlay.geometry(), self.host.rect())
        self.host.showFullScreen()
        self.app.processEvents()
        self.host._fitted_form.fit()
        self.assertEqual(self.overlay.geometry(), self.host.rect())
        self.host.showNormal()
        self.app.processEvents()
        self.assertEqual(self.overlay.geometry(), self.host.rect())
        self.assertTrue(self.overlay.busy)
        gate.set()
        wait_for(lambda: success.called)

    def test_visible_overlay_takes_keyboard_focus_and_stops_key_propagation(self):
        self.submit.setFocus()
        self.app.processEvents()
        recorder = KeyRecorder(self.host)
        operation, gate, started = self.blocked_operation("ready")
        success = Mock()
        self.overlay.run(operation, success, self.fail, show_delay_ms=0)
        wait_for(lambda: started.is_set() and self.overlay.isVisible())
        self.assertIs(self.app.focusWidget(), self.overlay)
        QTest.keyClick(self.app.focusWidget(), Qt.Key.Key_Return)
        QTest.keyClick(self.app.focusWidget(), Qt.Key.Key_A)
        QTest.keyClick(self.app.focusWidget(), Qt.Key.Key_Escape)
        self.assertEqual(recorder.keys, [])
        self.assertTrue(self.overlay.busy)
        gate.set()
        wait_for(lambda: success.called)
        self.assertIs(self.app.focusWidget(), self.submit)

    def test_tab_and_backtab_cannot_focus_underlying_enabled_controls(self):
        self.initially_disabled.setEnabled(True)
        operation, gate, started = self.blocked_operation("ready")
        success = Mock()
        self.overlay.run(operation, success, self.fail, show_delay_ms=0)
        wait_for(lambda: started.is_set() and self.overlay.isVisible())
        self.assertTrue(self.submit.isEnabled())
        self.assertTrue(self.initially_disabled.isEnabled())
        self.assertIs(self.app.focusWidget(), self.overlay)
        for key, modifiers in ((Qt.Key.Key_Tab, Qt.KeyboardModifier.NoModifier),
                               (Qt.Key.Key_Backtab, Qt.KeyboardModifier.NoModifier),
                               (Qt.Key.Key_Tab, Qt.KeyboardModifier.ShiftModifier)):
            QTest.keyClick(self.app.focusWidget(), key, modifiers)
            self.app.processEvents()
            self.assertIs(self.app.focusWidget(), self.overlay)
        gate.set()
        wait_for(lambda: success.called)

    def test_shutdown_suppresses_callbacks_while_job_still_has_current_overlay_token(self):
        result = object()
        operation, gate, started = self.blocked_operation(result)
        success, failure, dispose = Mock(), Mock(), Mock()
        self.overlay.run(operation, success, failure, dispose,
                         controls=(self.submit, self.initially_disabled))
        wait_for(started.is_set)
        job = self.overlay._job
        self.assertFalse(self.submit.isEnabled())
        # Release the worker first; shutdown may wait safely without GUI pumping.
        gate.set()
        job.shutdown()
        self.assertIs(self.overlay._job, job)
        self.assertTrue(self.overlay.busy)
        success.assert_not_called()
        failure.assert_not_called()
        wait_for(lambda: not _JOBS)
        self.assertFalse(self.overlay.busy)
        self.assertFalse(self.overlay.isVisible())
        self.assertTrue(self.submit.isEnabled())
        self.assertFalse(self.initially_disabled.isEnabled())
        dispose.assert_called_once_with(result)
        success.assert_not_called()
        failure.assert_not_called()


if __name__ == "__main__":
    unittest.main()
