"""Focused regression tests for offline user synchronization, credential safety, and account linking."""
import json
import os
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parents[2]
_BACKEND = _ROOT / "senyasabi"
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from argon2 import PasswordHasher
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend import auth_service
from backend.database import models, repository as repo
from backend.database.session import Base


class TestOfflineUserSync(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)
        db_path = Path(self.tmp.name, "test_sync.db").as_posix()
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)

        from contextlib import contextmanager

        @contextmanager
        def scope():
            s = self.Session()
            try:
                yield s
                s.commit()
            except Exception:
                s.rollback()
                raise
            finally:
                s.close()

        # Patch session_scope in auth_service and repository
        p1 = patch.object(auth_service, "session_scope", scope)
        p1.start()
        self.addCleanup(p1.stop)
        self.addCleanup(self.engine.dispose)

        auth_service._repository = auth_service.SQLiteUserRepository()
        auth_service.logout_user()

    def tearDown(self):
        auth_service.logout_user()

    def test_offline_registration_stores_locally_without_secrets(self):
        """Offline registration persists user locally and safely without exposing credentials."""
        with patch.object(auth_service.auth_client, "register", side_effect=auth_service.NetworkError("Offline")):
            res = auth_service.register_user(
                "offline_mary", "offline_mary@example.com", "SecretPassword123!", "Mary D"
            )
            self.assertEqual(res["username"], "offline_mary")
            self.assertEqual(res["email"], "offline_mary@example.com")
            self.assertNotIn("password", res)
            self.assertNotIn("password_hash", res)

        with self.Session() as db:
            # 1. User exists in SQLite users table
            user = repo.get_user_by_username(db, "offline_mary")
            self.assertIsNotNone(user)
            self.assertEqual(user.email, "offline_mary@example.com")

            # 2. Offline credentials exist with argon2id hash
            offline_auth = repo.get_offline_auth_by_identifier(db, "offline_mary")
            self.assertIsNotNone(offline_auth)
            self.assertTrue(offline_auth.password_verifier.startswith("$argon2id$"))
            self.assertTrue(PasswordHasher().verify(offline_auth.password_verifier, "SecretPassword123!"))

    def test_wrong_password_does_not_link_or_bypass_auth(self):
        """Invalid password for offline user raises AuthError and does not attempt remote registration."""
        with patch.object(auth_service.auth_client, "register", side_effect=auth_service.NetworkError("Offline")):
            auth_service.register_user("offline_tom", "tom@example.com", "CorrectPassword123", "Tom")

        with patch.object(auth_service.auth_client, "login", side_effect=auth_service.AuthError("Invalid login credentials")), \
             patch.object(auth_service.auth_client, "register") as mock_reg:
            with self.assertRaises(auth_service.AuthError):
                auth_service.authenticate_user("offline_tom", "WrongPassword999")
            mock_reg.assert_not_called()

    def test_reconnection_links_offline_user_and_migrates_id(self):
        """When an offline user logs in online, remote registration/login creates remote identity and migrates local records."""
        # 1. Register offline
        with patch.object(auth_service.auth_client, "register", side_effect=auth_service.NetworkError("Offline")):
            res = auth_service.register_user("link_user", "link_user@example.com", "Password12345", "Link")
            local_uid = uuid.UUID(res["user_id"])

        # 2. Create pending quiz attempts and sync queue under local_uid
        attempt_id = uuid.uuid4()
        sync_item_id = uuid.uuid4()
        with self.Session() as db:
            repo.upsert_quiz_attempt(
                db, user_id=local_uid, attempt_id=attempt_id, quiz_id=1,
                started_at=None, completed_at=None, score=85, max_score=100,
                percentage=85.0, passed=True
            )
            repo.enqueue_sync(
                db, sync_id=sync_item_id, user_id=local_uid, entity_type="quiz_attempt",
                entity_id=str(attempt_id), payload={"score": 85}, operation="upsert"
            )
            db.commit()

        # 3. Simulate reconnecting and logging in:
        # First remote login fails (user does not exist remotely yet in Supabase)
        # Then remote register succeeds
        # Then second remote login succeeds
        remote_uid = uuid.uuid4()
        mock_remote_login = {
            "session": {"access_token": "mock-jwt-token", "refresh_token": "mock-refresh", "expires_at": 9999999999},
            "profile": {"user_id": str(remote_uid), "username": "link_user", "email": "link_user@example.com", "display_name": "Link"}
        }

        with patch.object(auth_service.auth_client, "login", side_effect=[auth_service.AuthError("User not found"), mock_remote_login]) as mock_login, \
             patch.object(auth_service.auth_client, "register", return_value={"username": "link_user"}) as mock_reg:
            online_res = auth_service.authenticate_user("link_user", "Password12345")
            self.assertEqual(online_res["user_id"], remote_uid)
            self.assertEqual(auth_service.get_access_token(), "mock-jwt-token")
            mock_reg.assert_called_once_with("link_user", "link_user@example.com", "Password12345", "Link")

        # 4. Verify local SQLite records migrated from local_uid to remote_uid
        with self.Session() as db:
            # Old user record deleted or replaced
            self.assertIsNone(db.get(models.User, local_uid))
            self.assertIsNotNone(db.get(models.User, remote_uid))

            # Quiz attempt migrated
            attempt = db.get(models.QuizAttempt, attempt_id)
            self.assertIsNotNone(attempt)
            self.assertEqual(attempt.user_id, remote_uid)

            # Sync queue migrated
            queue_item = db.get(models.SyncQueue, sync_item_id)
            self.assertIsNotNone(queue_item)
            self.assertEqual(queue_item.user_id, remote_uid)

    def test_offline_login_fallback_when_network_unavailable(self):
        """When an offline-registered user logs in while still disconnected, authenticate_offline succeeds."""
        with patch.object(auth_service.auth_client, "register", side_effect=auth_service.NetworkError("Offline")):
            auth_service.register_user("still_offline", "still@example.com", "SecretPass123", "Still")

        # Login while still offline: login raises NetworkError
        with patch.object(auth_service.auth_client, "login", side_effect=auth_service.NetworkError("No connection")):
            res = auth_service.authenticate_user("still_offline", "SecretPass123")
            self.assertEqual(res["username"], "still_offline")
            self.assertIsNone(auth_service.get_access_token())

    def test_online_registration_preserves_standard_behavior(self):
        """When network is available, registration creates remote account normally via auth_client."""
        with patch.object(
            auth_service.auth_client,
            "register",
            return_value={"username": "online_user", "email": "online@example.com", "display_name": "Online User"},
        ) as mock_reg:
            res = auth_service.register_user("online_user", "online@example.com", "Pass123456", "Online User")
            mock_reg.assert_called_once_with("online_user", "online@example.com", "Pass123456", "Online User")
            self.assertEqual(res["username"], "online_user")

    def test_online_login_existing_remote_user_does_not_trigger_re_registration(self):
        """An already registered remote user logs in directly without triggering re-registration."""
        remote_uid = uuid.uuid4()
        mock_login_data = {
            "session": {"access_token": "token-xyz", "refresh_token": "refresh-xyz", "expires_at": 9999999999},
            "profile": {"user_id": str(remote_uid), "username": "existing_remote", "email": "remote@example.com", "display_name": "Remote"},
        }
        with patch.object(auth_service.auth_client, "login", return_value=mock_login_data) as mock_login, \
             patch.object(auth_service.auth_client, "register") as mock_reg:
            res = auth_service.authenticate_user("existing_remote@example.com", "Pass123456")
            self.assertEqual(res["user_id"], remote_uid)
            mock_reg.assert_not_called()



if __name__ == "__main__":
    unittest.main()
