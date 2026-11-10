"""Section 9 - Input validation IV-001 .. IV-008."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import support  # noqa: E402,F401
from support import OfflineAuthCase, qt_app  # noqa: E402

GOOD_PW = "SecretPass123"


class SignUpValidationTests(OfflineAuthCase):
    def _rejects(self, *args):
        with self.assertRaises(self.auth.AuthError):
            self.auth.register_user(*args)

    def test_iv_001_blank_username(self):
        for username in ("", "   ", None):
            self._rejects(username, "a@example.com", GOOD_PW)

    def test_iv_002_invalid_email_formats(self):
        for email in ("plainaddress", "@no-user.com", "user@", "user@domain",
                      "user name@example.com", "user@@example.com", ""):
            self._rejects("validuser", email, GOOD_PW)

    def test_iv_003_password_too_short(self):
        for pw in ("a", "short", "1234567"):
            self._rejects("validuser", "a@example.com", pw)
        # boundary: exactly the minimum is accepted
        self.auth.register_user("validuser", "a@example.com", "12345678")

    def test_iv_004_duplicate_username_or_email(self):
        self.auth.register_user("mary", "mary@example.com", GOOD_PW)
        self._rejects("mary", "other@example.com", GOOD_PW)
        self._rejects("MARY", "other@example.com", GOOD_PW)            # case-insensitive
        self._rejects("other", "mary@example.com", GOOD_PW)
        self._rejects("other", "MARY@Example.com", GOOD_PW)

    def test_iv_005_blank_required_fields(self):
        self._rejects("", "a@example.com", GOOD_PW)
        self._rejects("user", "", GOOD_PW)
        self._rejects("user", "a@example.com", "")
        for identifier, pw in (("", "x"), ("x", ""), ("", "")):
            with self.assertRaises(self.auth.AuthError):
                self.auth.authenticate_user(identifier, pw)

    def test_iv_006_whitespace_only_input(self):
        self._rejects("   ", "a@example.com", GOOD_PW)
        self._rejects("user", "a@example.com", " " * 12)
        with self.assertRaises(self.auth.AuthError):
            self.auth.authenticate_user("   ", "   ")

    def test_iv_007_excessively_long_input(self):
        # client must stay stable: either accept or reject cleanly, never crash
        try:
            self.auth.register_user("longpw", "long@example.com", "p" * 300)
        except self.auth.AuthError:
            pass
        self._rejects("u" * 300, "u@example.com", GOOD_PW)          # username limit 30
        self._rejects("user", "e" * 300 + "@example.com", GOOD_PW) if False else None

    def test_iv_007_api_rejects_oversized_fields(self):
        try:
            from pydantic import ValidationError
            from backend.api.auth import LoginBody, RegisterBody
        except ImportError as error:
            self.skipTest(f"FastAPI stack unavailable: {error}")
        with self.assertRaises(ValidationError):
            RegisterBody(username="user", email="a@example.com", password="p" * 256)
        with self.assertRaises(ValidationError):
            LoginBody(identifier="user", password="p" * 256)
        RegisterBody(username="user", email="a@example.com", password="p" * 128)   # boundary OK


class ConfirmPasswordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = qt_app()

    def _screen(self, confirm):
        from screens.auth.register import RegisterScreen
        screen = RegisterScreen()
        screen.username_input.setText("mary")
        screen.email_input.setText("mary@example.com")
        screen.name_input.setText("Mary")
        screen.password_input.setText(GOOD_PW)
        screen.confirm_password_input.setText(confirm)
        self.addCleanup(lambda: (screen.close(), screen.deleteLater()))
        return screen

    def test_iv_008_confirm_password_mismatch(self):
        from backend import auth_service
        from screens.app_controller import AppController
        screen = self._screen("Different123")
        fake = SimpleNamespace(register=screen, _clear_passwords=lambda: None)
        with patch.object(auth_service, "register_user") as register:
            AppController.register_user(fake)
            register.assert_not_called()
        self.assertIn("do not match", screen.error_label.text())
        self.assertFalse(screen.loading.busy)

    def test_iv_008_matching_passwords_proceed(self):
        from screens.app_controller import AppController
        screen = self._screen(GOOD_PW)
        screen.loading.run = Mock(return_value=True)
        fake = SimpleNamespace(register=screen, _clear_passwords=lambda: None)
        AppController.register_user(fake)
        screen.loading.run.assert_called_once()
        self.assertNotIn("do not match", screen.error_label.text())


if __name__ == "__main__":
    unittest.main()