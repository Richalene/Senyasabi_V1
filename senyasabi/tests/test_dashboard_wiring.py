"""Focused regression tests for Dashboard Progress Wiring & Synchronization."""
import sys
import tempfile
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parents[2]
_BACKEND = _ROOT / "senyasabi"
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend import auth_service, dashboard_service, progress_sync, sync_service
from backend.api_client import get_api_client
from backend.database import models, repository as repo
from backend.database.session import Base
from backend.sync_supabase import fetch_progress_snapshot


class TestDashboardWiring(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)
        db_path = Path(self.tmp.name, "test_dash.db").as_posix()
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)

        # Create v_user_statistics_live view
        schema_path = _BACKEND / "backend" / "database" / "sqlite_schema.sql"
        if schema_path.exists():
            schema_sql = schema_path.read_text(encoding="utf-8")
            view_start = schema_sql.find("CREATE VIEW IF NOT EXISTS v_user_statistics_live")
            if view_start != -1:
                # view ends at ; followed by newline or next comment
                view_end = schema_sql.find(";\n--", view_start)
                if view_end == -1:
                    view_end = schema_sql.find(";", view_start)
                with self.engine.begin() as conn:
                    conn.execute(text(schema_sql[view_start:view_end + 1]))

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

        for mod in (
            "backend.database.session.session_scope",
            "backend.progress_sync.session_scope",
            "backend.dashboard_service.session_scope",
            "backend.sync_service.session_scope",
            "backend.auth_service.session_scope",
        ):
            p = patch(mod, scope)
            p.start()
            self.addCleanup(p.stop)

        self.addCleanup(self.engine.dispose)

        auth_service._repository = auth_service.SQLiteUserRepository()
        auth_service.logout_user()

    def tearDown(self):
        auth_service.logout_user()

    def test_unauthenticated_snapshot_returns_none_safely(self):
        """When not logged in or without token, fetch_progress_snapshot returns None safely."""
        with patch.object(auth_service, "get_current_user", return_value=None):
            self.assertIsNone(fetch_progress_snapshot())

        with patch.object(auth_service, "get_current_user", return_value={"user_id": str(uuid.uuid4())}), \
             patch.object(auth_service, "get_access_token", return_value=None):
            self.assertIsNone(fetch_progress_snapshot())

    def test_authenticated_snapshot_attaches_jwt_and_restores_anon_key(self):
        """fetch_progress_snapshot sets user JWT during execution and restores anon key in finally block."""
        uid = str(uuid.uuid4())
        mock_user = {"user_id": uid, "username": "mary"}
        mock_token = "jwt-user-token-12345"

        mock_supabase = MagicMock()
        mock_supabase.supabase_key = "original-anon-key"
        mock_supabase.postgrest = MagicMock()

        # Mock PostgREST responses
        mock_data = [{"user_id": uid, "score": 100}]
        mock_exec = MagicMock()
        mock_exec.execute.return_value = MagicMock(data=mock_data)
        mock_table = MagicMock()
        mock_table.select.return_value.eq.return_value = mock_exec
        mock_supabase.table.return_value = mock_table

        with patch("backend.sync_supabase.get_supabase_client", return_value=mock_supabase), \
             patch.object(auth_service, "get_current_user", return_value=mock_user), \
             patch.object(auth_service, "get_access_token", return_value=mock_token):

            snapshot = fetch_progress_snapshot()

            self.assertIsNotNone(snapshot)
            # Verify auth was called with the user's token
            mock_supabase.postgrest.auth.assert_any_call(mock_token)
            # Verify auth was restored to the original anon key
            self.assertEqual(mock_supabase.postgrest.auth.call_args[0][0], "original-anon-key")

    def test_apply_snapshot_preserves_local_completed_status(self):
        """Applying a remote snapshot merges data without regressing local Completed status."""
        uid = uuid.uuid4()
        with self.Session() as db:
            cv = models.ContentVersion(version_number=1, changelog="init", is_published=True, is_deleted=False)
            db.add(cv)
            db.flush()
            user = models.User(user_id=uid, username="test_dash_user", email=None, display_name="Test")
            db.add(user)
            module = models.Module(module_id=1, module_code="alphabet", title="Alphabet", module_order=1, is_active=True, content_version_id=cv.content_version_id)
            db.add(module)
            lesson = models.Lesson(lesson_id=1, lesson_code="alpha_1", parent_module=1, title="Lesson 1", lesson_order=1, content_version_id=cv.content_version_id)
            db.add(lesson)
            db.flush()

            repo.create_or_update_lesson_progress(
                db, user_id=uid, lesson_id=1, completion_percentage=100.0,
                status="Completed", time_spent_seconds=60
            )
            db.commit()

        # Remote snapshot has 'In Progress' with 50%
        remote_snapshot = {
            "lesson_progress": [
                {
                    "user_id": str(uid),
                    "lesson_id": 1,
                    "completion_percentage": 50.0,
                    "status": "In Progress",
                    "time_spent_seconds": 30,
                    "last_accessed": datetime.now(timezone.utc).isoformat(),
                    "completed_at": None,
                    "client_updated_at": datetime.now(timezone.utc).isoformat(),
                }
            ],
            "quiz_attempts": [],
            "minigame_attempts": [],
            "user_badges": [],
            "streaks": [],
            "user_statistics": [],
        }

        with patch.object(auth_service, "get_current_user", return_value={"user_id": str(uid)}):
            counts = progress_sync.apply_snapshot(remote_snapshot)
            self.assertEqual(counts.get("lesson_progress"), 1)

        with self.Session() as db:
            lp = repo.get_lesson_progress(db, uid, 1)
            self.assertIsNotNone(lp)
            self.assertEqual(lp.status, "Completed")
            self.assertEqual(lp.completion_percentage, 100.0)

    def test_statistics_freshness_after_quiz_and_lesson(self):
        """Queueing local quiz attempts and lesson progress recalculates user_statistics."""
        uid = uuid.uuid4()
        with self.Session() as db:
            cv = models.ContentVersion(version_number=1, changelog="init", is_published=True, is_deleted=False)
            db.add(cv)
            db.flush()
            user = models.User(user_id=uid, username="test_stats_user", email=None, display_name="Test")
            db.add(user)
            module = models.Module(module_id=1, module_code="alphabet", title="Alphabet", module_order=1, is_active=True, content_version_id=cv.content_version_id)
            db.add(module)
            lesson = models.Lesson(lesson_id=1, lesson_code="alpha_1", parent_module=1, title="Lesson 1", lesson_order=1, content_version_id=cv.content_version_id)
            db.add(lesson)
            quiz = models.Quiz(quiz_id=1, quiz_code="q1", module_id=1, title="Q1", passing_score=70, content_version_id=cv.content_version_id)
            db.add(quiz)
            db.commit()

        # Queue lesson progress
        now = datetime.now(timezone.utc)
        sync_service.queue_lesson_progress(
            user_id=uid, lesson_id=1, completion_percentage=100.0,
            status="Completed", time_spent_seconds=120
        )

        # Queue quiz attempt
        attempt_id = uuid.uuid4()
        sync_service.queue_quiz_attempt(
            user_id=uid, attempt_id=attempt_id, quiz_id=1,
            started_at=now, completed_at=now,
            score=95, max_score=100, percentage=95.0, passed=True,
            duration_seconds=45
        )

        with self.Session() as db:
            stat = repo.get_user_statistics(db, uid)
            self.assertIsNotNone(stat)
            self.assertEqual(stat.lessons_completed, 1)
            self.assertEqual(stat.quizzes_completed, 1)
            self.assertEqual(stat.total_quiz_score, 95)
            self.assertAlmostEqual(stat.average_accuracy, 95.0)

    def test_dashboard_rank_fallback_to_remote_position(self):
        """When local leaderboard cache has no entry, get_dashboard_stats falls back to remote user position."""
        uid = str(uuid.uuid4())
        mock_position = {
            "user_id": uid,
            "board_code": "all_time",
            "rank_position": 4,
            "total_score": 250,
        }

        with patch.object(get_api_client(), "get_user_leaderboard_position", return_value=mock_position):
            stats = dashboard_service.get_dashboard_stats(uid)
            self.assertEqual(stats["leaderboard"]["rank_position"], 4)


if __name__ == "__main__":
    unittest.main()
