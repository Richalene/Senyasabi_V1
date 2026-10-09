"""Run: python -m unittest discover -s senyasabi/tests -v"""
import os
from pathlib import Path
import sys
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from argon2 import PasswordHasher
from backend import auth_service as auth
from PySide6.QtWidgets import QApplication, QPushButton
from screens.app_controller import AppController


class AuthTests(unittest.TestCase):
    def setUp(self):
        auth._repository = auth.InMemoryUserRepository()
        auth.logout_user()

    def test_signup_hash_and_safe_session(self):
        user = auth.register_user('mary', 'mary@example.com', 'secret', 'Mary')
        stored = auth._repository.find_by_identifier('mary')
        self.assertTrue(stored.password_hash.startswith('$argon2id$'))
        self.assertTrue(PasswordHasher().verify(stored.password_hash, 'secret'))
        self.assertEqual(set(vars(stored)), {'user_id', 'username', 'email', 'password_hash',
            'display_name', 'notifications_enabled', 'dark_mode', 'created_at', 'updated_at'})
        self.assertNotIn('password_hash', user)
        self.assertIsNone(auth.get_current_user())
        auth.authenticate_user('MARY@EXAMPLE.COM', 'secret')
        session = auth.get_current_user()
        self.assertNotIn('password', session)
        self.assertNotIn('password_hash', session)
        session['username'] = 'changed'
        self.assertEqual(auth.get_current_user()['username'], 'mary')

    def test_required_email_duplicates(self):
        for values in [('', 'a@b.com', 'p'), ('a', '', 'p'), ('a', 'a@b.com', ''),
                       ('a', 'a@b.com', '   '), ('a', 'invalid', 'p')]:
            with self.subTest(values=values), self.assertRaises(auth.AuthError):
                auth.register_user(*values)
        auth.register_user('mary', 'mary@example.com', 'secret')
        for values in [('MARY', 'other@example.com', 'p'), ('other', 'MARY@example.com', 'p')]:
            with self.subTest(values=values), self.assertRaises(auth.AuthError):
                auth.register_user(*values)

    def test_login_logout_repeated(self):
        auth.register_user('mary', 'mary@example.com', 'secret')
        for identifier in ['mary', 'mary@example.com'] * 3:
            self.assertEqual(auth.authenticate_user(identifier, 'secret')['username'], 'mary')
            auth.logout_user()
            self.assertIsNone(auth.get_current_user())
        for identifier, password in [('mary', 'wrong'), ('unknown', 'secret'), ('', 'secret'), ('mary', '')]:
            with self.subTest(identifier=identifier), self.assertRaises(auth.AuthError):
                auth.authenticate_user(identifier, password)
            self.assertIsNone(auth.get_current_user())


class NavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        auth._repository = auth.InMemoryUserRepository()
        auth.logout_user()
        self.controller = AppController()
        self.controller.show_login()

    def tearDown(self):
        for widget in (self.controller.welcome, self.controller.landing,
                       self.controller.login, self.controller.register,
                       self.controller.dashboard, self.controller.main_menu):
            widget.close()
            widget.deleteLater()
        self.app.processEvents()
        auth.logout_user()

    def click(self, screen, name):
        screen.findChild(QPushButton, name).click()
        self.app.processEvents()

    def assert_screen(self, expected):
        self.assertTrue(expected.isVisible())
        visible = [w for w in self.app.topLevelWidgets() if w.isVisible()]
        self.assertEqual(visible, [expected])

    def fill_signup(self, confirm='secret'):
        screen = self.controller.register
        screen.username_input.setText('mary')
        screen.email_input.setText('mary@example.com')
        screen.name_input.setText('Mary')
        screen.password_input.setText('secret')
        screen.confirm_password_input.setText(confirm)

    def test_complete_flow(self):
        c = self.controller
        self.assert_screen(c.login)
        c.show_dashboard()
        self.assert_screen(c.login)
        self.click(c.login, 'registerButton')
        self.assert_screen(c.register)
        self.fill_signup('different')
        self.click(c.register, 'createAccountButton')
        self.assertIn('match', c.register.error_label.text())
        self.assertIsNone(auth._repository.find_by_identifier('mary'))
        self.fill_signup()
        self.click(c.register, 'createAccountButton')
        self.assert_screen(c.login)
        self.assertFalse(c.register.password_input.text())
        self.click(c.login, 'registerButton')
        self.fill_signup()
        self.click(c.register, 'createAccountButton')
        self.assertIn('already', c.register.error_label.text())
        self.assert_screen(c.register)
        self.click(c.register, 'signInButton')
        self.assert_screen(c.login)
        c.login.password_input.setText('wrong')
        self.click(c.login, 'continueButton')
        self.assertIn('Invalid', c.login.error_label.text())
        self.assert_screen(c.login)
        self.assertIsNone(auth.get_current_user())
        for identifier in ['mary', 'mary@example.com', 'mary']:
            c.login.email_input.setText(identifier)
            c.login.password_input.setText('secret')
            self.click(c.login, 'continueButton')
            self.assert_screen(c.main_menu)
            self.assertFalse(c.login.password_input.text())
            self.assertEqual(auth.get_current_user()['display_name'], 'Mary')
            c.logout_button.click()
            self.app.processEvents()
            self.assert_screen(c.login)
            self.assertIsNone(auth.get_current_user())
            self.assertFalse(c.login.email_input.text())


if __name__ == '__main__':
    unittest.main()
