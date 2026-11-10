"""Section 10 - Database testing DB-001 .. DB-008 (real sqlite_schema.sql, FKs enforced)."""
import sqlite3
import sys
import unittest
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import support  # noqa: E402,F401
from support import TempDatabase, new_user, seed_content  # noqa: E402

from sqlalchemy.exc import IntegrityError  # noqa: E402


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        from backend.database import repository as repo, models as m
        self.repo, self.m = repo, m
        self.db = TempDatabase()
        self.addCleanup(self.db.close)
        with self.db.scope() as s:
            self.cv = seed_content(s)

    def test_db_001_insert(self):
        with self.db.scope() as s:
            uid = new_user(s)
            self.repo.create_or_update_lesson_progress(s, uid, 1, 50.0, "In Progress")
            self.repo.award_badge(s, uid, 1)
            self.repo.create_or_update_streak(s, uid, 1, 1, date.today())
        with self.db.scope() as s:
            for model in (self.m.User, self.m.LessonProgress, self.m.UserBadges, self.m.Streak):
                self.assertEqual(s.query(model).count(), 1, model.__name__)

    def test_db_002_select(self):
        with self.db.scope() as s:
            uid = new_user(s, "Reader")
            self.repo.create_sign(s, 1, "a", "A", "A", self.cv)
            self.repo.create_sign(s, 2, "b", "B", "B", self.cv)
            self.repo.link_sign_to_lesson(s, 1, 2, self.cv, display_order=1)
            self.repo.link_sign_to_lesson(s, 1, 1, self.cv, display_order=2)
        with self.db.scope() as s:
            username = self.repo.get_user_by_id(s, uid).username
            self.assertEqual(self.repo.get_user_by_username(s, username.upper()).user_id, uid)
            self.assertEqual(len(self.repo.list_modules(s)), 1)
            self.assertEqual([x.sign_code for x in self.repo.list_signs(s, lesson_id=1)], ["b", "a"])
            self.assertIsNone(self.repo.get_user_by_username(s, "nobody"))

    def test_db_003_update(self):
        with self.db.scope() as s:
            uid = new_user(s)
        with self.db.scope() as s:
            self.repo.update_user_profile(s, uid, display_name="Renamed")
            self.repo.update_lesson(s, 1, title="Renamed lesson")
            self.repo.update_quiz(s, 1, passing_score=85)
        with self.db.scope() as s:
            self.assertEqual(self.repo.get_user_by_id(s, uid).display_name, "Renamed")
            self.assertEqual(self.repo.get_lesson(s, 1).title, "Renamed lesson")
            self.assertEqual(self.repo.get_quiz(s, 1).passing_score, 85)

    def test_db_004_delete(self):
        with self.db.scope() as s:
            uid = new_user(s)
            self.repo.create_sign(s, 1, "a", "A", "A", self.cv)
        with self.db.scope() as s:
            self.assertTrue(self.repo.delete_user(s, uid))
            self.assertFalse(self.repo.delete_user(s, uid))
            self.assertTrue(self.repo.delete_sign(s, 1))                 # soft delete
        with self.db.scope() as s:
            self.assertIsNone(self.repo.get_user_by_id(s, uid))
            self.assertEqual(self.repo.list_signs(s), [])

    def test_db_005_duplicates_prevented(self):
        with self.db.scope() as s:
            self.repo.upsert_user(s, uuid.uuid4(), "Dupe", "a@example.com", "A")
            self.repo.create_sign(s, 1, "hello", "Hello", "HELLO", self.cv)
        with self.assertRaises(IntegrityError):
            with self.db.scope() as s:
                self.repo.upsert_user(s, uuid.uuid4(), "dupe", "b@example.com", "B")   # username, any case
        with self.assertRaises(IntegrityError):
            with self.db.scope() as s:
                self.repo.upsert_user(s, uuid.uuid4(), "other", "a@example.com", "B")  # email
        with self.assertRaises(IntegrityError):
            with self.db.scope() as s:
                self.repo.create_sign(s, 2, "hello", "Hello 2", "HELLO", self.cv)      # sign_code
        with self.db.scope() as s:                                                      # queue coalesces
            uid = new_user(s)
            for payload in ({"v": 1}, {"v": 2}):
                self.repo.enqueue_sync(s, uuid.uuid4(), uid, "lesson_progress", 1, payload)
            self.assertEqual(self.repo.get_sync_queue_stats(s, uid)["pending"], 1)

    def test_db_006_foreign_key_integrity(self):
        with self.assertRaises(IntegrityError):
            with self.db.scope() as s:
                self.repo.create_or_update_lesson_progress(s, uuid.uuid4(), 1)        # unknown user
        with self.db.scope() as s:
            uid = new_user(s)
        with self.assertRaises(IntegrityError):
            with self.db.scope() as s:
                self.repo.create_or_update_lesson_progress(s, uid, 999)               # unknown lesson
        with self.assertRaises(IntegrityError):
            with self.db.scope() as s:
                self.repo.upsert_quiz_attempt(s, uid, uuid.uuid4(), 999)              # unknown quiz

    def test_db_007_interrupted_save_leaves_consistent_data(self):
        with self.assertRaises(RuntimeError):
            with self.db.scope() as s:
                self.repo.upsert_user(s, uuid.uuid4(), "halfway", "h@example.com", "H")
                raise RuntimeError("crash mid-save")
        with self.assertRaises(IntegrityError):                                       # atomic batch
            with self.db.scope() as s:
                self.repo.upsert_user(s, uuid.uuid4(), "first", "1@example.com", "1")
                self.repo.upsert_user(s, uuid.uuid4(), "first", "2@example.com", "2")
        with self.db.scope() as s:
            self.assertEqual(s.query(self.m.User).count(), 0)
        conn = sqlite3.connect(self.db.path)                                          # process "dies"
        conn.isolation_level = None
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("INSERT INTO users (user_id, username) VALUES ('crash-user', 'crash')")
        conn.close()
        check = sqlite3.connect(self.db.path)
        try:
            self.assertEqual(check.execute("SELECT count(*) FROM users").fetchone()[0], 0)
            self.assertEqual(check.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        finally:
            check.close()

    def test_db_008_data_persists_across_restart(self):
        with self.db.scope() as s:
            uid = new_user(s)
            self.repo.create_or_update_lesson_progress(s, uid, 1, 100.0, "Completed")
            self.repo.create_or_update_streak(s, uid, 3, 5, date.today())
            self.repo.enqueue_sync(s, uuid.uuid4(), uid, "lesson_progress", 1, {"v": 1})
        self.db.reopen()                                  # logout + restart
        with self.db.scope() as s:
            self.assertIsNotNone(self.repo.get_user_by_id(s, uid))
            self.assertEqual(self.repo.get_lesson_progress(s, uid, 1).status, "Completed")
            self.assertEqual(self.repo.get_streak(s, uid).longest_streak, 5)
            self.assertEqual(len(self.repo.dequeue_pending_sync(s, user_id=uid)), 1)


if __name__ == "__main__":
    unittest.main()