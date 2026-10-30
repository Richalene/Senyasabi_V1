"""Data views fetch in workers while navigation and the loading animation stay live."""
import os
from pathlib import Path
import sys
from threading import Event, get_ident
from time import monotonic
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton
from backend import auth_service, dashboard_service, leaderboard_service
from screens.dashboard.dashboard import DashboardWindow, StatisticsDashboardWindow
from screens.dashboard.leaderboard import LeaderboardWindow
from screens.loading import _JOBS


def wait_until(predicate, timeout=3000):
    deadline = monotonic() + timeout / 1000
    while monotonic() < deadline:
        QApplication.processEvents()
        if predicate():
            return
        QTest.qWait(10)
    raise AssertionError("Data loading did not finish")


class DataLoadingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def setUp(self):
        self.windows = []
        self.releases = []
        auth_service._current_user = {"user_id": "first", "display_name": "First Learner"}

    def tearDown(self):
        for release in self.releases:
            release.set()
        for window in self.windows:
            window.close()
        wait_until(lambda: not _JOBS)
        for window in self.windows:
            window.deleteLater()
        self.app.processEvents()
        auth_service.logout_user()

    def window(self, kind):
        window = kind()
        self.windows.append(window)
        return window

    def release(self):
        release = Event()
        self.releases.append(release)
        return release

    def data(self, lessons):
        data = dashboard_service.DefaultDashboardRepository().get_dashboard_stats(None)
        data["user_statistics"]["lessons_completed"] = lessons
        return data

    def test_construction_does_not_query_repositories(self):
        with patch.object(dashboard_service, "get_dashboard_stats") as stats, \
             patch.object(leaderboard_service, "get_leaderboard") as leaderboard:
            for kind in (DashboardWindow, StatisticsDashboardWindow, LeaderboardWindow):
                self.window(kind)
            stats.assert_not_called()
            leaderboard.assert_not_called()

    def test_progress_refresh_keeps_ui_responsive_and_suppresses_duplicates(self):
        release = self.release()
        entered = Event()
        worker_threads = []
        main_thread = get_ident()

        def fetch(user_id):
            worker_threads.append(get_ident())
            entered.set()
            release.wait(2)
            return self.data(7)

        window = self.window(DashboardWindow)
        with patch.object(dashboard_service, "get_dashboard_stats", side_effect=fetch) as service:
            window.show()
            wait_until(entered.is_set)
            self.assertEqual(window.ui.welcomeLabel.text(), "Welcome Back, First Learner!")
            self.assertFalse(window.refresh_home_stats())
            self.assertFalse(window.refresh_home_stats())
            service.assert_called_once_with("first")
            heartbeat = []
            QTimer.singleShot(0, lambda: heartbeat.append(True))
            wait_until(lambda: window.loading.isVisible())
            self.assertTrue(heartbeat)
            self.assertNotEqual(worker_threads, [main_thread])
            window.resize(900, 600)
            self.app.processEvents()
            self.assertEqual(window.loading.geometry(), window.rect())
            release.set()
            wait_until(lambda: not window.loading.busy)
        self.assertEqual(window.ui.lblLessonsCompleted.text(), "7")
        self.assertFalse(window.loading.isVisible())
        self.assertFalse(window.loading.animation.isActive())

    def test_hidden_statistics_discard_completion(self):
        release = self.release()
        entered = Event()

        def fetch(user_id):
            entered.set()
            release.wait(2)
            return self.data(9)

        window = self.window(StatisticsDashboardWindow)
        with patch.object(dashboard_service, "get_dashboard_stats", side_effect=fetch):
            window.show()
            wait_until(entered.is_set)
            window.hide()
            release.set()
            wait_until(lambda: not _JOBS)
        self.assertEqual(window.ui.lblLessonsCompleted.text(), "0")
        self.assertFalse(window.loading.busy)
        self.assertFalse(window.loading.animation.isActive())

    def test_session_switch_cannot_restore_previous_progress(self):
        for kind in (DashboardWindow, StatisticsDashboardWindow):
            with self.subTest(kind=kind.__name__):
                release = self.release()
                entered = Event()

                def fetch(user_id):
                    if user_id == "first":
                        entered.set()
                        release.wait(2)
                        return self.data(99)
                    return self.data(2)

                auth_service._current_user = {"user_id": "first"}
                window = self.window(kind)
                with patch.object(dashboard_service, "get_dashboard_stats", side_effect=fetch) as service:
                    window.show()
                    wait_until(entered.is_set)
                    window.hide()
                    auth_service._current_user = {"user_id": "second"}
                    window.show()
                    wait_until(lambda: not window.loading.busy)
                    release.set()
                    wait_until(lambda: not _JOBS)
                    self.assertEqual(window.ui.lblLessonsCompleted.text(), "2")
                    self.assertEqual([call.args[0] for call in service.call_args_list], ["first", "second"])
                window.hide()

    def test_statistics_failure_offers_working_retry(self):
        for kind in (DashboardWindow, StatisticsDashboardWindow):
            with self.subTest(kind=kind.__name__):
                window = self.window(kind)
                with patch.object(dashboard_service, "get_dashboard_stats",
                                  side_effect=[RuntimeError("unavailable"), self.data(4)]):
                    window.show()
                    wait_until(lambda: not window.loading.busy)
                    self.assertTrue(window.data_status.isVisible())
                    self.assertTrue(window.data_status.retry.isEnabled())
                    window.data_status.retry.click()
                    wait_until(lambda: not window.loading.busy)
                    self.assertFalse(window.data_status.isVisible())
                    self.assertEqual(window.ui.lblLessonsCompleted.text(), "4")
                window.hide()

    def test_leaderboard_worker_uses_captured_user_and_recovers(self):
        entries = [dict(user_id="first", username="First", current_streak=3,
                        badges_unlocked=1, rank_position=1, is_current_user=True)]
        window = self.window(LeaderboardWindow)
        with patch.object(leaderboard_service, "get_leaderboard",
                          side_effect=[RuntimeError("unavailable"), entries]) as service:
            window.show()
            wait_until(lambda: not window.loading.busy)
            retry = window.ui.leaderboardContainer.findChild(QPushButton)
            self.assertIsNotNone(retry)
            retry.click()
            wait_until(lambda: not window.loading.busy)
            self.assertEqual(window.ui.lblCurrentStreak.text(), "3 Days")
            self.assertEqual(window.ui.leaderboardLayout.count(), 1)
            for call in service.call_args_list:
                self.assertEqual(call.kwargs, {"user_id": "first"})

    def test_leaderboard_explicit_user_does_not_read_current_session(self):
        mock_entries = [dict(user_id="mock-2", username="Sample Ben", total_score=100, current_streak=5, badges_unlocked=2, rank_position=1)]
        with patch.object(leaderboard_service._repository, "get_leaderboard", return_value=mock_entries):
            with patch.object(auth_service, "get_current_user", side_effect=AssertionError("GUI snapshot required")):
                entries = leaderboard_service.get_leaderboard(user_id="mock-2")
        self.assertEqual([entry["user_id"] for entry in entries if entry["is_current_user"]], ["mock-2"])
