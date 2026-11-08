"""Comprehensive tests for logout behavior across all SenyaSabi pages.

Verifies:
- Logout from Main Menu, Statistics Dashboard, Leaderboard, and Minigames.
- AppController.logout() is the single source of truth.
- auth_service.logout_user() is called exactly once.
- LoginScreen becomes visible and previous authenticated screens are hidden.
- Back navigation behavior is preserved.
- Repeated logout clicks do not cause duplicate cleanup or navigation errors.
- Tests use mocked auth without contacting live Supabase.
"""
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch, MagicMock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication
from screens.app_controller import AppController
from backend import auth_service
from screens.dialogs import MenuCalloutPopup


class LogoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        # Ensure fresh controller and mocked offline environment
        p1 = patch("backend.progress_sync.pull_user_progress", return_value=False)
        p1.start()
        self.addCleanup(p1.stop)
        p2 = patch("backend.supabase_client.get_supabase_client", return_value=None)
        p2.start()
        self.addCleanup(p2.stop)
        p3 = patch("backend.auth_service.get_credential_store")
        p3.start()
        self.addCleanup(p3.stop)

        self.controller = AppController()
        auth_service.logout_user()

    def tearDown(self):
        auth_service.logout_user()
        for window in (self.controller.welcome, self.controller.landing,
                       self.controller.login, self.controller.register,
                       self.controller.main_menu, self.controller.dashboard,
                       getattr(self.controller.dashboard, "_leaderboard", None),
                       self.controller.minigames):
            if window is not None:
                window.close()
        self.app.processEvents()

    def _set_authenticated_session(self, user_id="test-logout-user"):
        user = {"user_id": user_id, "email": "test@example.com", "username": "testuser"}
        auth_service._current_user = user
        auth_service._session = {"access_token": "mock-token", "refresh_token": "mock-refresh"}
        return user

    def _find_popup(self, parent_widget):
        popups = parent_widget.findChildren(MenuCalloutPopup)
        if popups:
            return popups[0]
        # If not already instantiated, clicking the menu button creates it
        if hasattr(parent_widget, "header") and parent_widget.header is not None:
            if parent_widget.header.menu_button is not None:
                parent_widget.header.menu_button.click()
                popups = parent_widget.findChildren(MenuCalloutPopup)
                if popups:
                    return popups[0]
        return None

    def test_logout_from_main_menu(self):
        self._set_authenticated_session()
        self.controller.show_main_menu()
        self.assertTrue(self.controller.main_menu.isVisible())

        popup = self._find_popup(self.controller.main_menu)
        self.assertIsNotNone(popup, "MenuCalloutPopup should be present on main menu")
        popup._on_sign_out()
        self.app.processEvents()

        self.assertIsNone(auth_service.get_current_user())
        self.assertFalse(self.controller.main_menu.isVisible())
        self.assertTrue(self.controller.login.isVisible())

    def test_logout_from_statistics_dashboard(self):
        self._set_authenticated_session()
        self.controller.show_dashboard()
        self.assertTrue(self.controller.dashboard.isVisible())

        popup = self._find_popup(self.controller.dashboard)
        self.assertIsNotNone(popup, "MenuCalloutPopup should be present on statistics dashboard")
        popup._on_sign_out()
        self.app.processEvents()

        self.assertIsNone(auth_service.get_current_user())
        self.assertFalse(self.controller.dashboard.isVisible())
        self.assertTrue(self.controller.login.isVisible())

    def test_logout_from_leaderboard(self):
        self._set_authenticated_session()
        self.controller.show_dashboard()
        self.controller.dashboard._open_leaderboard()
        lb = self.controller.dashboard._leaderboard
        self.assertIsNotNone(lb)
        self.assertTrue(lb.isVisible())

        popup = self._find_popup(lb)
        self.assertIsNotNone(popup, "MenuCalloutPopup should be present on leaderboard")
        popup._on_sign_out()
        self.app.processEvents()

        self.assertIsNone(auth_service.get_current_user())
        self.assertFalse(lb.isVisible())
        self.assertFalse(self.controller.dashboard.isVisible())
        self.assertTrue(self.controller.login.isVisible())

    def test_logout_from_minigames(self):
        self._set_authenticated_session()
        self.controller.show_minigames()
        self.assertIsNotNone(self.controller.minigames)
        self.assertTrue(self.controller.minigames.isVisible())

        popup = self._find_popup(self.controller.minigames)
        self.assertIsNotNone(popup, "MenuCalloutPopup should be present on minigames menu")
        popup._on_sign_out()
        self.app.processEvents()

        self.assertIsNone(auth_service.get_current_user())
        self.assertFalse(self.controller.minigames.isVisible())
        self.assertTrue(self.controller.login.isVisible())

    def test_authentication_cleared_exactly_once(self):
        self._set_authenticated_session()
        self.controller.show_dashboard()

        real_logout = auth_service.logout_user
        call_count = 0

        def counting_logout():
            nonlocal call_count
            call_count += 1
            real_logout()

        with patch.object(auth_service, "logout_user", side_effect=counting_logout):
            popup = self._find_popup(self.controller.dashboard)
            popup._on_sign_out()
            self.app.processEvents()

        self.assertEqual(call_count, 1, "auth_service.logout_user() should be called exactly once")
        self.assertIsNone(auth_service.get_current_user())
        self.assertTrue(self.controller.login.isVisible())

    def test_repeated_logout_clicks_safe(self):
        self._set_authenticated_session()
        self.controller.show_main_menu()

        popup = self._find_popup(self.controller.main_menu)
        # Simulate double/rapid clicking on logout
        popup._on_sign_out()
        popup._on_sign_out()
        self.controller.logout()  # direct call after already logged out
        self.app.processEvents()

        self.assertIsNone(auth_service.get_current_user())
        self.assertTrue(self.controller.login.isVisible())
        self.assertFalse(self.controller.main_menu.isVisible())

    def test_back_navigation_preserved(self):
        self._set_authenticated_session()
        self.controller.show_dashboard()
        self.assertTrue(self.controller.dashboard.isVisible())

        # Clicking back on dashboard should return to main menu, NOT log out
        self.controller.dashboard.ui.btnBack.click()
        self.app.processEvents()
        self.assertIsNotNone(auth_service.get_current_user(), "Back button must not log out")
        self.assertFalse(self.controller.dashboard.isVisible())
        self.assertTrue(self.controller.main_menu.isVisible())

        # Test leaderboard back button
        self.controller.show_dashboard()
        self.controller.dashboard._open_leaderboard()
        lb = self.controller.dashboard._leaderboard
        self.assertTrue(lb.isVisible())
        lb.ui.btnBack.click()
        self.app.processEvents()
        self.assertIsNotNone(auth_service.get_current_user(), "Leaderboard back must not log out")
        self.assertFalse(lb.isVisible())
        self.assertTrue(self.controller.dashboard.isVisible())

        # Test minigames back button
        self.controller.show_minigames()
        self.assertTrue(self.controller.minigames.isVisible())
        self.controller.minigames.back_button.click()
        self.app.processEvents()
        self.assertIsNotNone(auth_service.get_current_user(), "Minigames back must not log out")
        self.assertFalse(self.controller.minigames.isVisible())
        self.assertTrue(self.controller.main_menu.isVisible())

    def test_lesson_select_hamburger_returns_to_main_menu(self):
        self._set_authenticated_session()
        # Open lesson select for a module
        self.controller.selected_module = "alphabet"
        self.controller.show_module_choices("alphabet")
        self.assertIsNotNone(self.controller.module_lessons)
        self.assertTrue(self.controller.module_lessons.isVisible())

        # Clicking hamburger on LessonSelectWidget emits menu_requested -> show_main_menu
        self.controller.module_lessons.header.menu_button.click()
        self.app.processEvents()
        self.assertIsNotNone(auth_service.get_current_user(), "Lesson select menu button must not log out")
        self.assertTrue(self.controller.main_menu.isVisible())
        self.assertFalse(self.controller.module_lessons.isVisible())

    def test_fallback_controller_lookup_when_unwired(self):
        self._set_authenticated_session()
        from PySide6.QtWidgets import QWidget, QPushButton
        from screens.dialogs import MenuCalloutPopup

        # Create a dummy widget that doesn't define logout_requested
        dummy = QWidget()
        dummy.btn = QPushButton(dummy)
        dummy.show()

        popup = MenuCalloutPopup(dummy.btn)
        popup._on_sign_out()
        self.app.processEvents()

        # The fallback should locate AppController and execute logout cleanly
        self.assertIsNone(auth_service.get_current_user())
        self.assertTrue(self.controller.login.isVisible())
        dummy.close()


if __name__ == "__main__":
    unittest.main()
