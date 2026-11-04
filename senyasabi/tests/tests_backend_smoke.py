"""Run alone: python -m unittest tests.test_backend_smoke -v
(the env var must be set before backend.database is first imported)"""
import os, sys, tempfile, unittest, uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

_TMP = tempfile.TemporaryDirectory()
os.environ["SENYASABI_DB"] = str(Path(_TMP.name) / "test.db")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from argon2 import PasswordHasher
from sqlalchemy.exc import IntegrityError

from backend import auth_service, dashboard_service, sync_service
from backend.credential_store import InMemoryCredentialStore
from backend.database import repository as repo
from backend.database.init_db import initialize_database
from backend.database.session import session_scope

NOW = lambda: datetime.now(timezone.utc)


def new_user(username="mary", password=None):
    uid = uuid.uuid4()
    with session_scope() as db:
        repo.upsert_user(db, uid, f"{username}_{uid.hex[:6]}", f"{uid.hex[:8]}@example.com", "Mary")
        if password:
            repo.upsert_offline_auth(db, uid, PasswordHasher().hash(password), NOW())
    return uid


class BackendSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        initialize_database()
        with session_scope() as db:
            cv = repo.get_content_version_by_number(db, 1).content_version_id
            repo.create_module(db, 1, "WORD", "Words", cv, 1)
            repo.create_lesson(db, 1, "WORD_GREETING", "Greeting", cv, 1, 1)
            repo.create_quiz(db, quiz_id=1, quiz_code="WORD_QUIZ", module_id=1,
                             content_version_id=cv, title="Word Quiz")
            repo.create_minigame(db, minigame_id=1, minigame_code="sign_sprint", module_id=1,
                                 content_version_id=cv, game_name="Sign Sprint",
                                 game_type="camera", config={"rounds": 5})
            repo.create_badge(db, 1, "FIRST_STEPS", "First Steps", "Complete a lesson")

    @classmethod
    def tearDownClass(cls):
        from backend.database.engine import engine
        engine.dispose()
        try:
            _TMP.cleanup()
        except Exception:
            pass

    def test_seed_readable(self):
        with session_scope() as db:
            self.assertEqual(len(repo.list_modules(db)), 1)
            self.assertEqual(repo.get_minigame(db, 1).config, {"rounds": 5})  # JSON round-trip

    def test_foreign_keys_enforced(self):
        with self.assertRaises(IntegrityError):
            with session_scope() as db:
                repo.create_or_update_lesson_progress(db, uuid.uuid4(), 1)

    def test_lesson_progress_and_queue_coalescing(self):
        uid = new_user()
        sync_service.queue_lesson_progress(uid, 1, 50.0, "In Progress", 30)
        sync_service.queue_lesson_progress(uid, 1, 100.0, "Completed", 20)
        self.assertEqual(sync_service.get_sync_status(uid)["pending"], 1)  # coalesced
        with session_scope() as db:
            p = repo.get_lesson_progress(db, uid, 1)
            self.assertEqual(p.time_spent_seconds, 50)
            self.assertIsNotNone(p.completed_at)
            self.assertIsNotNone(p.completed_at.tzinfo)                    # UTC-aware
        with patch.object(sync_service.SyncService, "_send_to_server", return_value=True):
            res = sync_service.process_pending_syncs(uid, batch_size=100)
        self.assertEqual(res["failed"], 0)
        self.assertEqual(sync_service.get_sync_status(uid)["pending"], 0)
        sync_service.queue_lesson_progress(uid, 1, 100.0, "Completed", 5)  # after sync: new row OK
        self.assertEqual(sync_service.get_sync_status(uid)["pending"], 1)

    def test_naive_datetime_rejected(self):
        uid = new_user()
        with self.assertRaises(ValueError):
            sync_service.queue_quiz_attempt(uid, uuid.uuid4(), 1, datetime.now(), NOW(),
                                            8, 10, 80.0, True)

    def test_quiz_minigame_stats_dashboard(self):
        uid = new_user()
        start = NOW() - timedelta(minutes=2)
        sync_service.queue_lesson_progress(uid, 1, 100.0, "Completed", 60)
        sync_service.queue_quiz_attempt(uid, uuid.uuid4(), 1, start, NOW(), 8, 10, 80.0, True,
                                        duration_seconds=120, camera_accuracy=70.0, mc_accuracy=90.0)
        sync_service.queue_minigame_attempt(uid, uuid.uuid4(), 1, start, NOW(), 40, 60, 75.0)
        with session_scope() as db:
            repo.create_or_update_streak(db, uid, 3, 3, date.today())
            repo.award_badge(db, uid, 1)
        repo.rebuild_user_statistics(*_db_and(uid))
        d = dashboard_service.get_dashboard_stats(uid)
        s = d["user_statistics"]
        self.assertEqual((s["lessons_completed"], s["quizzes_completed"],
                          s["minigames_completed"], s["total_quiz_score"]), (1, 1, 1, 8))
        self.assertEqual(d["streaks"]["current_streak"], 3)
        self.assertEqual(len(d["user_badges"]), 1)
        self.assertEqual(d["module_count"], 1)
        with session_scope() as db:
            perf = repo.get_module_performance(db, uid)[0]
            self.assertEqual(perf["score"], 75.0)          # 0.5*80 + 0.5*70
            self.assertEqual(repo.get_latest_badge(db, uid)[0].badge_code, "FIRST_STEPS")

    def test_offline_login_and_lockout(self):
        uid = new_user(password="secret123")
        with session_scope() as db:
            username = repo.get_user_by_id(db, uid).username
        with patch.object(auth_service, "get_credential_store", return_value=InMemoryCredentialStore):
            user = auth_service.authenticate_offline(username, "secret123")
            self.assertEqual(user["user_id"], uid)
            for _ in range(4):
                with self.assertRaises(auth_service.AuthError):
                    auth_service.authenticate_offline(username, "wrong")
            with self.assertRaisesRegex(auth_service.AuthError, "Locked"):
                auth_service.authenticate_offline(username, "wrong")
            with self.assertRaisesRegex(auth_service.AuthError, "Too many"):
                auth_service.authenticate_offline(username, "secret123")  # locked even if correct
            self.assertIsNone(auth_service.get_current_user())


def _db_and(uid):
    # rebuild_user_statistics needs a Session; return (session, uid) with a manual lifetime
    from backend.database.session import SessionLocal
    db = SessionLocal()
    return db, uid


if __name__ == "__main__":
    unittest.main()