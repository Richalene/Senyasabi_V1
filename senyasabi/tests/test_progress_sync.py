import sys
import tempfile
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from backend import progress_sync
from backend.database import models as m
from backend.database.session import Base

UID = str(uuid.UUID(int=7))


class ProgressSyncTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(tmp.cleanup)
        engine = create_engine(f"sqlite:///{Path(tmp.name, 't.db').as_posix()}")
        event.listen(engine, "connect", lambda c, _: c.execute("PRAGMA foreign_keys=ON"))
        self.addCleanup(engine.dispose)
        Base.metadata.create_all(engine)
        self.Session = sessionmaker(bind=engine, expire_on_commit=False)

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
        p = patch.object(progress_sync, "sync_content_if_due", return_value=True)
        p.start()
        self.addCleanup(p.stop)
        with scope() as db:
            db.add(m.ContentVersion(version_number=1, changelog="x", is_published=True, is_deleted=False))
            db.flush()
            cv = db.query(m.ContentVersion).one().content_version_id
            db.add(m.User(user_id=uuid.UUID(UID), username="u", email=None, display_name="U"))
            db.add(m.Module(module_code="alphabet", title="A", module_order=1, is_active=True,
                            is_deleted=False, content_version_id=cv))
            db.flush()
            mod = db.query(m.Module).one().module_id
            db.add(m.Lesson(lesson_code="l1", title="L", parent_module=mod, lesson_order=1, is_active=True,
                            is_deleted=False, content_version_id=cv))
            db.add(m.Badge(badge_code="B", badge_name="First Steps", is_deleted=False))
            db.flush()

    def snapshot(self, pct=100):
        return {
            "lesson_progress": [dict(user_id=UID, lesson_id=1, completion_percentage=pct, status="Completed",
                                     last_accessed="2026-10-17T10:00:00+00:00",
                                     completed_at="2026-10-17T10:00:00+00:00", time_spent_seconds=300,
                                     client_updated_at="2026-10-17T10:00:00+00:00",
                                     updated_at="2026-10-17T10:00:00+00:00")],
            "user_badges": [dict(user_id=UID, badge_id=1, unlocked_at="2026-10-17T10:00:00+00:00")],
            "streaks": [dict(user_id=UID, current_streak=3, longest_streak=5,
                             last_activity_date="2026-10-17", updated_at="2026-10-17T10:00:00+00:00")],
            "user_statistics": [dict(user_id=UID, lessons_completed=1, quizzes_completed=0, minigames_completed=0,
                                     total_quiz_score=0, total_minigame_score=0, average_accuracy=None,
                                     total_time_spent_seconds=300, updated_at="2026-10-17T10:00:00+00:00")],
        }

    def test_apply_merges_rows_and_is_idempotent(self):
        for _ in range(2):
            counts = progress_sync.apply_snapshot(self.snapshot())
        self.assertEqual(counts["lesson_progress"], 1)
        with self.Session() as s:
            self.assertEqual(s.query(m.LessonProgress).count(), 1)
            self.assertEqual(s.query(m.UserBadges).count(), 1)
            self.assertEqual(s.query(m.Streak).one().current_streak, 3)
            self.assertEqual(s.query(m.UserStatistics).one().lessons_completed, 1)

    def test_server_value_updates_existing_row_without_deleting_others(self):
        progress_sync.apply_snapshot(self.snapshot(pct=50))
        progress_sync.apply_snapshot(self.snapshot(pct=100))
        with self.Session() as s:
            self.assertEqual(float(s.query(m.LessonProgress).one().completion_percentage), 100.0)

    def test_pull_is_skipped_without_session_and_never_raises(self):
        with patch.object(progress_sync.auth_service, "get_access_token", return_value=None), \
                patch.object(progress_sync, "fetch_snapshot") as fetch:
            self.assertFalse(progress_sync.pull_user_progress())
            fetch.assert_not_called()
        with patch.object(progress_sync.auth_service, "get_access_token", return_value="t"), \
                patch.object(progress_sync, "fetch_snapshot", return_value=None):
            self.assertFalse(progress_sync.pull_user_progress())
        bad = {"lesson_progress": [dict(user_id=UID, lesson_id=999)]}  # FK violation: content not cached
        with patch.object(progress_sync.auth_service, "get_access_token", return_value="t"), \
                patch.object(progress_sync, "fetch_snapshot", return_value=bad):
            self.assertFalse(progress_sync.pull_user_progress())

    def test_successful_pull_returns_true(self):
        with patch.object(progress_sync.auth_service, "get_access_token", return_value="t"), \
                patch.object(progress_sync, "fetch_snapshot", return_value=self.snapshot()), \
                patch("backend.leaderboard_service.get_leaderboard", return_value=[]):
            self.assertTrue(progress_sync.pull_user_progress())


if __name__ == "__main__":
    unittest.main()

