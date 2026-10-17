"""Authentication work stays responsive and cancelled results cannot log users in."""
from contextlib import nullcontext
import os
from pathlib import Path
import sys
from threading import Event
from time import monotonic
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QCoreApplication, QEvent, QThread, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton

from backend import auth_service as auth
from screens.app_controller import AppController
from screens.loading import _JOBS


USER = {
    "user_id": "loading-test-user", "username": "mary",
    "display_name": "Mary", "email": "mary@example.com",
    "notifications_enabled": True, "dark_mode": False,
}


class AuthLoadingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        auth._repository = auth.InMemoryUserRepository()
        auth.logout_user()
        self.release_events = []
        self.controller = AppController()
        self.controller.show_login()
        self.app.processEvents()

    def tearDown(self):
        # No running QThread may outlive the widgets receiving its delivery.
        for event in self.release_events:
            event.set()
        self.controller.shutdown()
        self.wait_until(lambda: not _JOBS)
        c = self.controller
        for widget in (c.welcome, c.landing, c.login, c.register,
                       c.dashboard, c.main_menu, c.dashboard._leaderboard):
            if widget is not None:
                widget.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()
        auth.logout_user()

    def wait_until(self, predicate, timeout=5):
        deadline = monotonic() + timeout
        while not predicate() and monotonic() < deadline:
            QTest.qWait(5)
        self.assertTrue(predicate(), "Timed out waiting for authentication UI")

    def fill_login(self):
        screen = self.controller.login
        screen.email_input.setText("mary@example.com")
        screen.password_input.setText("secret")
        return screen

    def fill_signup(self):
        self.controller.show_register()
        screen = self.controller.register
        screen.username_input.setText("mary")
        screen.email_input.setText("mary@example.com")
        screen.name_input.setText("Mary")
        screen.password_input.setText("secret")
        screen.confirm_password_input.setText("secret")
        return screen

    def delayed_operation(self, *, error=None):
        started, release = Event(), Event()
        self.release_events.append(release)

        def operation(*args, **kwargs):
            started.set()
            if not release.wait(timeout=5):
                raise AssertionError("Authentication test did not release its worker")
            if error is not None:
                raise error
            return dict(USER)

        return operation, started, release

    def test_signin_responsive_single_submission_and_gui_session_commit(self):
        c = self.controller
        screen = self.fill_login()
        submit = screen.findChild(QPushButton, "continueButton")
        operation, started, release = self.delayed_operation()
        ticks, commits, worker_threads = [], [], []
        heartbeat = QTimer(screen)
        heartbeat.setInterval(10)
        heartbeat.timeout.connect(lambda: ticks.append(True))
        heartbeat.start()
        original_commit = auth.establish_session

        def verify(*args, **kwargs):
            worker_threads.append(QThread.currentThread())
            return operation(*args, **kwargs)

        def commit(user):
            commits.append(QThread.currentThread())
            return original_commit(user)

        with patch.object(auth, "authenticate_user", side_effect=verify) as authenticate:
            with patch.object(auth, "establish_session", side_effect=commit):
                submit.click()
                self.assertTrue(started.wait(timeout=2))
                self.assertTrue(screen.loading.busy)
                self.assertFalse(screen.password_input.text())
                self.assertFalse(submit.isEnabled())
                if hasattr(screen, "dev_button"):
                    self.assertFalse(screen.dev_button.isEnabled())
                submit.click()
                c.login_user()
                c.login_user()
                QTest.qWait(230)
                self.assertGreater(len(ticks), 3)
                self.assertTrue(screen.loading.isVisible())
                self.assertTrue(screen.loading.animation.isActive())
                authenticate.assert_called_once_with("mary@example.com", "secret",
                                                     establish_session=False)
                self.assertNotEqual(worker_threads, [self.app.thread()])
                self.assertIsNone(auth.get_current_user())

                job = screen.loading._job
                release.set()
                self.assertTrue(job.wait(2000))
                # The worker has finished; its queued GUI delivery has not run.
                self.assertIsNone(auth.get_current_user())
                self.assertEqual(commits, [])
                self.wait_until(lambda: not screen.loading.busy)
                self.assertEqual(commits, [self.app.thread()])
        heartbeat.stop()
        self.assertTrue(c.main_menu.isVisible())
        self.assertFalse(screen.isVisible())
        self.assertEqual(auth.get_current_user()["username"], "mary")
        self.assertFalse(screen.loading.isVisible())
        self.assertFalse(screen.loading.animation.isActive())

    def test_signup_responsive_single_submission_and_success(self):
        c = self.controller
        screen = self.fill_signup()
        submit = screen.findChild(QPushButton, "createAccountButton")
        operation, started, release = self.delayed_operation()
        ticks = []
        heartbeat = QTimer(screen)
        heartbeat.setInterval(10)
        heartbeat.timeout.connect(lambda: ticks.append(True))
        heartbeat.start()
        with patch.object(auth, "register_user", side_effect=operation) as register:
            submit.click()
            self.assertTrue(started.wait(timeout=2))
            self.assertTrue(screen.loading.busy)
            self.assertFalse(screen.password_input.text())
            self.assertFalse(screen.confirm_password_input.text())
            self.assertFalse(submit.isEnabled())
            submit.click()
            c.register_user()
            c.register_user()
            QTest.qWait(230)
            self.assertGreater(len(ticks), 3)
            self.assertTrue(screen.loading.isVisible())
            register.assert_called_once_with("mary", "mary@example.com", "secret", "Mary")
            release.set()
            self.wait_until(lambda: not screen.loading.busy)
        heartbeat.stop()
        self.assertTrue(c.login.isVisible())
        self.assertEqual(c.login.email_input.text(), "mary")
        self.assertIn("Account created", c.login.error_label.text())
        self.assertFalse(screen.username_input.text())
        self.assertFalse(screen.email_input.text())
        self.assertFalse(screen.name_input.text())
        self.assertIsNone(auth.get_current_user())

    def check_failure_and_retry(self, kind, error):
        c = self.controller
        auth.logout_user()
        if kind == "login":
            c.show_login()
            screen = self.fill_login()
            action = c.login_user
            service = "authenticate_user"
            submit_name = "continueButton"
        else:
            screen = self.fill_signup()
            action = c.register_user
            service = "register_user"
            submit_name = "createAccountButton"
        submit = screen.findChild(QPushButton, submit_name)
        operation, started, release = self.delayed_operation(error=error)
        log = (self.assertLogs("screens.app_controller", level="WARNING")
               if not isinstance(error, auth.AuthError) else nullcontext())
        with patch.object(auth, service, side_effect=operation):
            with log:
                action()
                self.assertTrue(started.wait(timeout=2))
                self.assertFalse(submit.isEnabled())
                release.set()
                self.wait_until(lambda: not screen.loading.busy)
        self.assertTrue(screen.isVisible())
        self.assertTrue(submit.isEnabled())
        self.assertFalse(screen.loading.isVisible())
        self.assertFalse(screen.password_input.text())
        self.assertIsNone(auth.get_current_user())
        if isinstance(error, auth.AuthError):
            self.assertEqual(screen.error_label.text(), str(error))
        else:
            self.assertIn("Please try again", screen.error_label.text())
            self.assertNotIn(str(error), screen.error_label.text())

        screen.password_input.setText("retry-secret")
        if kind == "register":
            screen.confirm_password_input.setText("retry-secret")
        with patch.object(auth, service, return_value=dict(USER)) as retry:
            submit.click()
            self.wait_until(lambda: not screen.loading.busy)
            retry.assert_called_once()
        self.assertTrue((c.main_menu if kind == "login" else c.login).isVisible())

    def test_signin_errors_restore_form_and_allow_retry(self):
        for error in (auth.AuthError("Invalid username/email or password."),
                      RuntimeError("Private backend failure containing secret")):
            with self.subTest(error=type(error).__name__):
                self.check_failure_and_retry("login", error)

    def test_signup_errors_restore_form_and_allow_retry(self):
        for error in (auth.AuthError("Username is already registered."),
                      RuntimeError("Private backend failure containing secret")):
            with self.subTest(error=type(error).__name__):
                self.check_failure_and_retry("register", error)

    def test_navigating_away_or_logout_discards_late_signin(self):
        c = self.controller
        for navigation in ("away", "logout"):
            with self.subTest(navigation=navigation):
                c.show_login()
                screen = self.fill_login()
                operation, started, release = self.delayed_operation()
                with patch.object(auth, "authenticate_user", side_effect=operation) as authenticate:
                    with patch.object(auth, "establish_session") as commit:
                        c.login_user()
                        self.assertTrue(started.wait(timeout=2))
                        if navigation == "away":
                            c.show_register()
                            expected = c.register
                        else:
                            c.logout()
                            expected = c.login
                        self.assertFalse(screen.loading.busy)
                        self.assertTrue(screen._ui.isEnabled())
                        release.set()
                        self.wait_until(lambda: not _JOBS)
                        authenticate.assert_called_once_with("mary@example.com", "secret",
                                                             establish_session=False)
                        commit.assert_not_called()
                self.assertTrue(expected.isVisible())
                self.assertFalse(c.main_menu.isVisible())
                self.assertIsNone(auth.get_current_user())

    def test_registration_password_mismatch_does_not_start_loading(self):
        screen = self.fill_signup()
        screen.confirm_password_input.setText("different")
        with patch.object(auth, "register_user") as register:
            self.controller.register_user()
            register.assert_not_called()
        self.assertIn("do not match", screen.error_label.text())
        self.assertFalse(screen.loading.busy)
        self.assertFalse(screen.loading.isVisible())
        self.assertTrue(screen._ui.isEnabled())
        self.assertFalse(screen.password_input.text())
        self.assertFalse(screen.confirm_password_input.text())


if __name__ == "__main__":
    unittest.main()
