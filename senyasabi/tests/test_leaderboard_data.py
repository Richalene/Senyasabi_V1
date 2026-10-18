import os
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from backend import leaderboard_service as svc
from backend.database import models
from backend.database.session import Base
from screens.dashboard.leaderboard import LeaderboardWindow

IDS = [str(uuid.UUID(int=i + 1)) for i in range(4)]


def api(entries):
    return {"board_code": "all_time", "entries": entries}


def row(i, name, score, rank, streak=0, badges=0):
    return dict(user_id=IDS[i], display_name=name, total_score=score, rank_position=rank,
                current_streak=streak, badge_count=badges)


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)
        engine = create_engine(f"sqlite:///{Path(self.tmp.name, 't.db').as_posix()}")
        event.listen(engine, "connect", lambda c, _: c.execute("PRAGMA foreign_keys=ON"))
        Base.metadata.create_all(engine)
        self.Session = sessionmaker(bind=engine, expire_on_commit=False)
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
        patcher = patch("backend.database.session.session_scope", scope)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(engine.dispose)

    def fetch(self, payload):
        return patch.object(svc.SyncedLeaderboardRepository, "_fetch", return_value=payload)

    def test_ranking_scores_and_current_user(self):
        data = [row(0, "Ana", 500, 1, 7, 3), row(1, "Ben", 300, 2), row(2, "Kai", 100, 3)]
        with self.fetch(api(data)):
            out = svc.get_leaderboard(user_id=IDS[1])
        self.assertEqual([e["rank_position"] for e in out], [1, 2, 3])
        self.assertEqual([e["total_score"] for e in out], [500, 300, 100])
        self.assertEqual([e["is_current_user"] for e in out], [False, True, False])
        self.assertEqual(out[0]["badges_unlocked"], 3)
        self.assertFalse(any("email" in e for e in out))

    def test_ties_share_rank_and_order_is_deterministic(self):
        data = [row(2, "zed", 200, 2), row(1, "Bob", 200, 2), row(0, "Amy", 400, 1), row(3, "bob", 200, 2)]
        with self.fetch(api(data)):
            a = svc.get_leaderboard(user_id=None)
        with self.fetch(api(list(reversed(data)))):
            b = svc.get_leaderboard(user_id=None)
        self.assertEqual(a, b)
        self.assertEqual([e["username"] for e in a], ["Amy", "Bob", "bob", "zed"])
        self.assertEqual([e["rank_position"] for e in a], [1, 2, 2, 2])

    def test_empty_board_is_not_an_error(self):
        with self.fetch(api([])):
            self.assertEqual(svc.get_leaderboard(user_id=None), [])

    def test_offline_uses_cache_written_by_last_online_fetch(self):
        data = [row(0, "Ana", 500, 1), row(1, "Ben", 300, 2)]
        with self.fetch(api(data)):
            svc.get_leaderboard(user_id=None)
        with self.fetch(None):
            out = svc.get_leaderboard(user_id=IDS[0])
        self.assertEqual([(e["username"], e["total_score"]) for e in out], [("Ana", 500), ("Ben", 300)])
        self.assertTrue(out[0]["is_current_user"])
        with self.Session() as s:
            self.assertTrue(all(u.email is None for u in s.query(models.User)))

    def test_cache_is_replaced_not_accumulated(self):
        with self.fetch(api([row(0, "Ana", 5, 1), row(1, "Ben", 3, 2)])):
            svc.get_leaderboard(user_id=None)
        with self.fetch(api([row(1, "Ben", 9, 1)])):
            svc.get_leaderboard(user_id=None)
        with self.fetch(None):
            out = svc.get_leaderboard(user_id=None)
        self.assertEqual([(e["username"], e["total_score"]) for e in out], [("Ben", 9)])

    def test_unavailable_when_offline_and_uncached(self):
        with self.fetch(None), self.assertRaises(svc.LeaderboardUnavailable):
            svc.get_leaderboard(user_id=None)

    def test_periods_validated_and_boards_cached_separately(self):
        with self.assertRaises(ValueError):
            svc.get_leaderboard(user_id=None, board_code="yearly")
        with self.fetch(api([row(0, "Ana", 5, 1)])):
            svc.get_leaderboard(user_id=None, board_code="weekly")
        with self.fetch(None):
            self.assertEqual(len(svc.get_leaderboard(user_id=None, board_code="weekly")), 1)
            with self.assertRaises(svc.LeaderboardUnavailable):
                svc.get_leaderboard(user_id=None, board_code="monthly")

    def test_notify_calls_and_removes_listeners(self):
        calls = []
        svc.add_scores_listener(lambda: calls.append(1))
        svc.notify_scores_changed()
        self.assertEqual(calls, [1])
        svc._listeners.clear()


class WindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = LeaderboardWindow()

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def wait(self):
        for _ in range(300):
            self.app.processEvents()
            if not self.window.loading.busy:
                self.app.processEvents()
                return
            QTest.qWait(10)
        self.fail("refresh did not finish")

    def texts(self):
        layout = self.window.ui.leaderboardLayout
        out = []
        for i in range(layout.count()):
            w = layout.itemAt(i).widget()
            out.append([w.text()] if isinstance(w, QLabel) else [l.text() for l in w.findChildren(QLabel)])
        return out

    def test_shows_name_and_points_and_refreshes_on_score_update(self):
        first = [dict(user_id="1", username="Ana", total_score=120, rank_position=1)]
        second = [dict(user_id="1", username="Ana", total_score=450, rank_position=1)]
        with patch.object(svc._repository, "get_leaderboard", return_value=first):
            self.window.show()
            self.wait()
            self.assertIn("120 pts", self.texts()[0])
            self.assertIn("Ana", self.texts()[0])
        with patch.object(svc._repository, "get_leaderboard", return_value=second):
            svc.notify_scores_changed()
            self.wait()
            self.assertIn("450 pts", self.texts()[0])

    def test_hidden_window_does_not_refresh_and_error_state_has_retry(self):
        with patch.object(svc._repository, "get_leaderboard", side_effect=svc.LeaderboardUnavailable("x")):
            svc.notify_scores_changed()
            self.assertFalse(self.window.loading.busy)
            self.window.show()
            self.wait()
            self.assertIn("couldn't load", self.texts()[0][0] if self.texts() else "")
        with patch.object(svc._repository, "get_leaderboard", return_value=[]):
            self.window.refresh()
            self.wait()
            self.assertEqual(self.window.ui.leaderboardLayout.count(), 1)
            self.assertEqual(self.texts()[0][0], "No leaderboard entries yet.")

    def test_set_board_loads_requested_period(self):
        with patch.object(svc, "get_leaderboard", return_value=[]) as g:
            self.window.show()
            self.wait()
            self.window.set_board("weekly")
            self.wait()
            self.assertEqual(g.call_args.kwargs["board_code"], "weekly")
        with self.assertRaises(ValueError):
            self.window.set_board("yearly")


if __name__ == "__main__":
    unittest.main()

