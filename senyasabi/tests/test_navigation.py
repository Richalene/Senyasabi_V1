import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton
from backend import auth_service
from screens.app_controller import AppController


class NavigationRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_authenticated_routes_reuse_windows_and_logout(self):
        c = AppController()
        user = {"user_id": "nav-user"}
        try:
            with patch.object(auth_service, "get_current_user", return_value=user), patch.object(auth_service, "authenticate_user", return_value=user):
                c.show_login()
                c.login_user()
                self.assert_only(c.main_menu)
                self.assertIs(c.dashboard._menu, c.main_menu)
                c.main_menu.ui.btnStartLearning.click()
                self.assert_only(c.main_menu._lesson_select)
                c.main_menu._lesson_select._ui.findChild(QPushButton, "backBtn").click()
                self.assert_only(c.main_menu)
                self.assertFalse(hasattr(c.main_menu.ui, "alphabetBtn"))
                self.assertFalse(hasattr(c.main_menu.ui, "wordLessonsBtn"))
                with patch.object(QMessageBox, "information") as notice:
                    c.main_menu.ui.btnMinigames.click()
                    notice.assert_called_once()
                self.assert_only(c.main_menu)
                for _ in range(3):
                    for card in (
                        c.main_menu.ui.btnLessonsCompleted,
                        c.main_menu.ui.btnModule,
                        c.main_menu.ui.btnLatestBadge,
                        c.main_menu.ui.btnLeaderboardRank,
                    ):
                        card.click()
                        self.assert_only(c.dashboard)
                        c.dashboard.ui.btnBack.click()
                        self.assert_only(c.main_menu)
                    c.show_dashboard()
                    c.dashboard.ui.btnLeaderboard.click()
                    self.assert_only(c.dashboard._leaderboard)
                    c.dashboard._leaderboard.ui.btnBack.click()
                    self.assert_only(c.dashboard)
                    c.dashboard.ui.btnBack.click()
                    self.assert_only(c.main_menu)
                    self.assertEqual(auth_service.get_current_user(), user)
                c.show_dashboard()
                c.dashboard.ui.btnLeaderboard.click()
                with patch.object(auth_service, "logout_user") as logout:
                    c.main_menu.logout_action.trigger()
                    logout.assert_called_once_with()
                self.assert_only(c.login)
        finally:
            for widget in (c.welcome, c.landing, c.login, c.register,
                           c.dashboard._leaderboard, c.dashboard, c.main_menu):
                if widget is not None:
                    widget.close()
                    widget.deleteLater()
            self.app.processEvents()

    def assert_only(self, screen):
        self.app.processEvents()
        self.assertEqual([w for w in self.app.topLevelWidgets() if w.isVisible()], [screen])
