import sys
import unittest
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend import auth_service


class BackgroundLoginTokenTests(unittest.TestCase):
    """UI logins run with establish_session=False; the token must still reach the API client."""

    def setUp(self):
        auth_service._clear_session()
        self.addCleanup(auth_service._clear_session)
        self.uid = uuid.uuid4()
        self.data = {"profile": {"user_id": str(self.uid), "username": "u", "email": None, "display_name": "U"},
                     "session": {"access_token": "tok", "refresh_token": "ref", "expires_at": 9999999999}}

    def login_in_background(self):
        scope = MagicMock()
        public = {"user_id": self.uid, "username": "u", "email": None, "display_name": "U"}
        with patch.object(auth_service, "session_scope", return_value=scope), \
                patch.object(auth_service.repo, "upsert_user"), \
                patch.object(auth_service.repo, "upsert_offline_auth"), \
                patch.object(auth_service, "_public_user", return_value=public), \
                patch.object(auth_service, "get_credential_store"):
            return auth_service._complete_online_login(self.data, "pw", establish_session=False)

    def test_token_available_only_after_ui_publishes_session(self):
        user = self.login_in_background()
        self.assertIsNone(auth_service.get_access_token())  # not published yet: no session
        with patch.object(auth_service, "get_credential_store"):
            auth_service.establish_session(user)
            self.assertEqual(auth_service.get_access_token(), "tok")

    def test_cancelled_login_leaves_no_session_and_logout_clears_pending(self):
        self.login_in_background()
        auth_service._clear_session()
        self.assertEqual(auth_service._pending_tokens, {})
        self.assertIsNone(auth_service.get_access_token())


if __name__ == "__main__":
    unittest.main()

