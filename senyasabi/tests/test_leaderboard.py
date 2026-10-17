import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend import auth_service, leaderboard_service
from PySide6.QtWidgets import QApplication, QLabel
from PySide6.QtTest import QTest
from screens.dashboard.dashboard import StatisticsDashboardWindow
from screens.dashboard.leaderboard import LeaderboardWindow


class LeaderboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = LeaderboardWindow()

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def entries(self, count):
        return [dict(user_id=str(i), username=f"User {i}", current_streak=i,
                     badges_unlocked=i % 4, rank_position=i) for i in range(count, 0, -1)]

    def wait_for_data(self):
        for _ in range(300):
            self.app.processEvents()
            if not self.window.loading.busy:
                self.app.processEvents()
                return
            QTest.qWait(10)
        self.fail("Leaderboard refresh did not finish")

    def test_empty_and_anonymous(self):
        with patch.object(leaderboard_service._repository, "get_leaderboard", return_value=[]):
            self.window.show()
            self.wait_for_data()
            self.assertEqual(self.window.ui.leaderboardLayout.count(), 1)
            self.assertEqual(self.window.ui.lblCurrentStreak.text(), "0 Days")
        with patch.object(auth_service, "get_current_user", return_value=None):
            self.assertFalse(any(row["is_current_user"] for row in leaderboard_service.get_leaderboard()))

    def test_many_users_order_highlight_scroll_and_refresh(self):
        entries = self.entries(100)
        with patch.object(leaderboard_service._repository, "get_leaderboard", return_value=entries), patch.object(auth_service, "get_current_user", return_value={"user_id": "42"}):
            data = leaderboard_service.get_leaderboard()
            self.assertEqual([row["rank_position"] for row in data], list(range(1, 101)))
            self.assertEqual(sum(row["is_current_user"] for row in data), 1)
            self.assertNotIn("is_current_user", entries[0])
            self.window.show()
            self.wait_for_data()
            self.window.refresh()
            self.wait_for_data()
            layout = self.window.ui.leaderboardLayout
            self.assertEqual(layout.count(), 100)
            self.assertEqual(layout.itemAt(0).widget().findChild(QLabel, "rank").text(), "🥇")
            self.assertEqual(layout.itemAt(0).widget().property("rank_position"), 1)
            current = layout.itemAt(41).widget()
            self.assertEqual(current.property("class"), "leaderboardCurrentUser")
            self.assertEqual(current.property("rank_position"), 42)
            self.assertEqual(current.findChild(QLabel, "username").text(), "YOU")
            self.assertEqual(self.window.ui.lblCurrentStreak.text(), "42 Days")
            scrollbar = self.window.ui.scrollLeaderboard.verticalScrollBar()
            self.assertGreater(scrollbar.maximum(), 0)
            scrollbar.setValue(scrollbar.maximum())
            self.assertEqual(scrollbar.value(), scrollbar.maximum())

    def test_dashboard_back_and_shared_hamburger(self):
        dashboard = StatisticsDashboardWindow()
        try:
            with patch.object(auth_service, "get_current_user", return_value={"user_id": "42"}):
                dashboard.show()
                dashboard.ui.btnLeaderboard.click()
                self.app.processEvents()
                self.assertFalse(dashboard.isVisible())
                self.assertTrue(dashboard._leaderboard.isVisible())
                dashboard._leaderboard.ui.btnBack.click()
                self.assertTrue(dashboard.isVisible())
                self.assertFalse(dashboard._leaderboard.isVisible())
                dashboard.ui.btnLeaderboard.click()
                for _ in range(300):
                    self.app.processEvents()
                    if not dashboard._leaderboard.loading.busy:
                        break
                    QTest.qWait(10)
                dashboard._leaderboard.ui.btnMenu.click()
                menu = dashboard._leaderboard.header.menu_button.menu()
                self.assertTrue(menu.isVisible())
                self.assertTrue(dashboard._leaderboard.isVisible())
                self.assertFalse(dashboard.isVisible())
                self.assertIsNone(dashboard._menu)
                menu.close()
                dashboard._leaderboard.ui.btnBack.click()
                self.assertTrue(dashboard.isVisible())
        finally:
            dashboard.close()
            for widget in (dashboard._leaderboard, dashboard._menu, dashboard):
                if widget is not None:
                    widget.deleteLater()
            self.app.processEvents()
