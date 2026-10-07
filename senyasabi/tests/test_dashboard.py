"""Run with the project's Python environment (Qt uses offscreen rendering)."""
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend import auth_service, dashboard_service
from PySide6.QtWidgets import QApplication
from screens.dashboard.dashboard import StatisticsDashboardWindow


class DashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        auth_service.logout_user()
        self.window = StatisticsDashboardWindow()

    def tearDown(self):
        self.window.close()
        if self.window._menu is not None:
            self.window._menu.deleteLater()
        self.window.deleteLater()
        self.app.processEvents()

    def test_defaults_and_fresh_data(self):
        data = dashboard_service.get_dashboard_stats("new-user")
        self.assertTrue(all(value == 0 for value in data["user_statistics"].values()))
        self.assertEqual(data["module_progress"], [])
        self.assertEqual(data["user_badges"], [])
        data["streaks"]["current_streak"] = 99
        self.assertEqual(dashboard_service.get_dashboard_stats("other")["streaks"]["current_streak"], 0)
        ui = self.window.ui
        for name in ("lblLessonsCompleted", "lblTotalQuizScore", "lblModuleCount", "lblMinigamesCompleted"):
            self.assertEqual(getattr(ui, name).text(), "0")
        self.assertEqual(ui.lblCurrentStreak.text(), "0 Days")
        self.assertEqual(ui.lblLatestBadge.text(), "No badges yet")
        self.assertEqual(ui.lblLeaderboardRank.text(), "Unranked")
        self.assertTrue(ui.btnLeaderboard.isEnabled())

    def test_session_lookup_and_rendering(self):
        data = dashboard_service.get_dashboard_stats("user-42")
        data["user_statistics"]["lessons_completed"] = 3
        data["module_progress"] = [dict(completion_percentage=50, status="in_progress", last_accessed=None, completed_at=None)]
        data["user_badges"] = [dict(badge_id="first", unlocked_at="2026-01-01")]
        data["leaderboard"]["rank_position"] = 2
        with patch.object(auth_service, "get_current_user", return_value={"user_id": "user-42"}), patch.object(dashboard_service, "get_dashboard_stats", return_value=data) as service:
            self.window.show()
            self.app.processEvents()
            service.assert_called_with("user-42")
        self.assertEqual(self.window.ui.lblLessonsCompleted.text(), "3")
        self.assertEqual(self.window.ui.lblModuleCount.text(), "1")
        self.assertEqual(self.window.ui.lblLatestBadge.text(), "first")
        self.assertEqual(self.window.ui.lblLeaderboardRank.text(), "#2")

    def test_existing_menu_navigation_and_anonymous_guard(self):
        self.window.ui.btnMenu.click()
        self.assertIsNone(self.window._menu)
        with patch.object(auth_service, "get_current_user", return_value={"user_id": "user-42"}):
            for button in (self.window.ui.btnBack, self.window.ui.btnMenu):
                self.window.show()
                button.click()
                self.app.processEvents()
                self.assertFalse(self.window.isVisible())
                self.assertTrue(self.window._menu.isVisible())
                self.window._menu.hide()
