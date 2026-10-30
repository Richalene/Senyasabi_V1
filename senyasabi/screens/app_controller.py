import logging
from PySide6.QtWidgets import QLineEdit

from screens.auth import login as dev_config
from screens.auth.login import LoginScreen
from screens.auth.register import RegisterScreen
from screens.startup import WelcomeScreen, LandingScreen
from screens.dashboard.dashboard import DashboardWindow, StatisticsDashboardWindow
from backend import auth_service


class AppController:
    def __init__(self):
        self.welcome = WelcomeScreen()
        self.landing = LandingScreen()
        self.login = LoginScreen()
        self.register = RegisterScreen()
        self.dashboard = StatisticsDashboardWindow()
        self.main_menu = DashboardWindow()
        self.minigames = None
        self.module_map = None
        self.module_lessons = None
        self.quiz = None
        self.active_lesson = None
        self.camera_settings = None
        self.selected_module = None
        self.main_menu.ui.btnStartLearning.clicked.disconnect()
        self.main_menu.ui.btnStartLearning.clicked.connect(self.show_module_map)
        self.main_menu.ui.btnMinigames.clicked.disconnect()
        self.main_menu.ui.btnMinigames.clicked.connect(self.show_minigames)
        self.dashboard._menu = self.main_menu
        self.dashboard.ui.btnBack.clicked.disconnect()
        self.dashboard.ui.btnBack.clicked.connect(self.show_main_menu)
        self.main_menu.stats_requested.connect(self.show_dashboard)
        self.main_menu.logout_requested.connect(self.logout)
        self.main_menu.camera_settings_requested.connect(self.show_camera_settings)

        self.login.dev_login_requested.connect(self.dev_login)
        self.register.dev_login_requested.connect(self.dev_login)
        self.login.continue_requested.connect(self.login_user)
        self.login.register_requested.connect(self.show_register)
        self.login.back_requested.connect(self.show_landing)
        self.register.back_requested.connect(self.show_landing)
        self.register.sign_in_requested.connect(self.show_login)
        self.register.create_account_requested.connect(self.register_user)
        self.welcome.ui.btnContinue.clicked.connect(self.show_landing)
        self.landing.ui.btnGetStarted.clicked.connect(self.show_register)
        self.landing.ui.btnLogin.clicked.connect(self.show_login)

    def _show_screen(self, screen):
        # Reuse each screen and show the destination before hiding the source.
        screen.show()
        windows = [self.welcome, self.landing, self.login, self.register,
                   self.main_menu, self.dashboard, self.dashboard._leaderboard, self.minigames, self.module_map, self.module_lessons,
                   self.quiz, self.active_lesson]
        windows.extend(getattr(self.main_menu, name, None) for name in (
            "_alphabet_menu", "_lesson_select", "_learn_window", "_spell_cat",
            "_spell_words", "_spell_lesson", "_word_menu", "_word_lesson"))
        from shiboken6 import isValid
        for window in windows:
            if window is None:
                continue
            if window is not screen:
                try:
                    if isValid(window):
                        window.hide()
                except Exception:
                    pass

    def show_welcome(self):
        self._show_screen(self.welcome)

    def show_landing(self):
        self._show_screen(self.landing)

    def _clear_passwords(self):
        self.login.password_input.clear()
        self.register.password_input.clear()
        if hasattr(self.register, 'confirm_password_input'):
            self.register.confirm_password_input.clear()

    def dev_login(self):
        if not dev_config.DEV_MODE:
            return
        # TEMPORARY: use the existing in-memory session; never persist a dev account.
        auth_service._current_user = {
            "user_id": "dev-session", "username": "dev",
            "display_name": "Dev User", "email": "dev@example.invalid",
            "notifications_enabled": False, "dark_mode": False,
        }
        self._clear_passwords()
        self.show_main_menu()

    def login_user(self):
        screen = self.login
        if screen.loading.busy:
            return
        identifier, password = screen.email_input.text(), screen.password_input.text()
        screen.error_label.clear()
        self._clear_passwords()
        auth_service.logout_user()

        def signed_in(user):
            auth_service.establish_session(user)
            self.show_main_menu()

        screen.loading.run(
            lambda: auth_service.authenticate_user(identifier, password, establish_session=False),
            signed_in, lambda error: self._auth_failed(screen, error, "sign you in"),
            message="Signing you in…", controls=self._auth_controls(screen))

    @staticmethod
    def _auth_controls(screen):
        return (screen._ui, screen.dev_button) if hasattr(screen, "dev_button") else (screen._ui,)

    @staticmethod
    def _auth_failed(screen, error, action):
        if isinstance(error, auth_service.AuthError):
            screen.error_label.setText(str(error))
        else:
            logging.getLogger(__name__).warning("Authentication unavailable: %s", type(error).__name__)
            screen.error_label.setText(f"We couldn’t {action}. Please try again.")

    def register_user(self):
        screen = self.register
        if screen.loading.busy:
            return
        password = screen.password_input.text()
        confirm_widget = screen._ui.findChild(QLineEdit, "confirmPasswordInput")
        confirm_text = screen.confirm_password_input.text() if hasattr(screen, "confirm_password_input") else ""
        email = screen.email_input.text().strip()
        screen.error_label.clear()
        self._clear_passwords()

        if (confirm_widget is not None or confirm_text) and password != confirm_text:
            screen.error_label.setText("Passwords do not match.")
            return

        if not email:
            screen.error_label.setText("Please enter your email.")
            return

        username = getattr(screen, "username_input", None)
        username = username.text().strip() if (username and username.text().strip()) else email.split("@")[0]
        # Clean username to match regex ^[a-z0-9_.-]{3,30}$
        import re
        username = re.sub(r"[^a-z0-9_.-]", "_", username.lower())
        if len(username) < 3:
            username = (username + "_user")[:30]

        name = getattr(screen, "name_input", None)
        name = name.text().strip() if (name and name.text().strip()) else username

        def registered(user):
            self.login.email_input.setText(user.get("username") or email)
            self.show_login()
            self.login.error_label.setText(
                "Account created. Check your email to confirm it, then sign in."
                if user.get("needs_confirmation")
                else "Account created. Sign in to continue.")
            screen.email_input.clear()
            screen.password_input.clear()
            if hasattr(screen, "username_input") and screen.username_input is not None:
                screen.username_input.clear()
            if hasattr(screen, "name_input") and screen.name_input is not None:
                screen.name_input.clear()

        screen.loading.run(lambda: auth_service.register_user(username, email, password, name),
                           registered, lambda error: self._auth_failed(screen, error, "create your account"),
                           message="Creating your account…", controls=self._auth_controls(screen))

    def logout(self):
        self.login.loading.cancel()
        self.register.loading.cancel()
        if self.camera_settings is not None:
            self.camera_settings.reject()
        auth_service.logout_user()
        self.selected_module = None
        self.login.email_input.clear()
        self.show_login()

    def show_login(self):
        self._clear_passwords()
        self.login.error_label.clear()
        self._show_screen(self.login)

    def show_register(self):
        self._clear_passwords()
        self.register.error_label.clear()
        self._show_screen(self.register)

    def show_dashboard(self):
        if auth_service.get_current_user() is None:
            self.show_login()
            return
        self._show_screen(self.dashboard)

    def show_main_menu(self):
        if auth_service.get_current_user() is None:
            self.show_login()
            return
        self._show_screen(self.main_menu)

    def show_minigames(self):
        if auth_service.get_current_user() is None:
            self.show_login()
            return
        screen = self._minigame_screen()
        screen.show_global_hub()
        self._show_screen(screen)

    def _minigame_screen(self):
        if self.minigames is None:
            from screens.minigames.minigame_select import MinigameSelect
            self.minigames = MinigameSelect()
            self.minigames.back_requested.connect(self.back_from_minigames)
        return self.minigames

    def show_module_map(self):
        if auth_service.get_current_user() is None:
            self.show_login()
            return
        if self.module_map is None:
            from screens.main_menu.module_select import ModuleSelectWidget
            self.module_map = ModuleSelectWidget()
            self.module_map.go_back.connect(self.show_main_menu)
            self.module_map.module_chosen.connect(self.open_module)
        self._show_screen(self.module_map)

    def open_module(self, code):
        self.show_module_choices(code)

    def show_module_choices(self, code=None):
        if auth_service.get_current_user() is None:
            self.show_login()
            return
        code = code or self.selected_module
        if code is None:
            self.show_module_map()
            return
        self.selected_module = code.lower()
        if self.module_lessons is None:
            from screens.main_menu.lesson_select import LessonSelectWidget
            self.module_lessons = LessonSelectWidget(module_code=self.selected_module)
            self.module_lessons.go_back.connect(self.show_module_map)
            self.module_lessons.menu_requested.connect(self.show_main_menu)
            self.module_lessons.lesson_chosen.connect(self.open_module_lesson)
            self.module_lessons.game_chosen.connect(self.open_module_game)
            self.module_lessons.quiz_requested.connect(self.open_module_quiz)
        else:
            self.module_lessons.set_module(self.selected_module)
        self.module_lessons.set_streak(self.main_menu.ui.streakValue.text())
        self._show_screen(self.module_lessons)

    def open_module_lesson(self, number):
        if auth_service.get_current_user() is None:
            self.show_login()
            return
        if self.selected_module is None:
            self.show_module_map()
            return
        if self.active_lesson is not None and self.active_lesson.isVisible():
            return
        self._dispose_lesson()
        if self.selected_module == "alphabet":
            from screens.lessons.alphabet.alphabet_lesson import AlphabetLessonWidget
            screen = AlphabetLessonWidget(lesson_number=number)
        else:
            from backend.content_service import get_words_for_lesson, get_words_for_module
            words = get_words_for_lesson(self.selected_module, number) or get_words_for_module(self.selected_module)
            from screens.lessons.words.word_lesson import WordLessonWidget
            screen = WordLessonWidget(words, self.selected_module)
        self.active_lesson = screen
        screen.lesson_finished.connect(self._lesson_back)
        self._show_screen(screen)

    def _dispose_lesson(self):
        screen, self.active_lesson = self.active_lesson, None
        if screen is not None:
            try:
                screen.lesson_finished.disconnect(self._lesson_back)
            except Exception:
                pass
            try:
                from shiboken6 import isValid
                if isValid(screen):
                    screen.close()
                    screen.deleteLater()
            except Exception:
                pass

    def _lesson_back(self):
        try:
            self.main_menu.refresh_home_stats()
        except Exception:
            pass
        self.show_module_choices()

    def open_module_quiz(self):
        if auth_service.get_current_user() is None:
            self.show_login()
            return
        if self.selected_module is None:
            self.show_module_map()
            return
        if self.quiz is not None and self.quiz.isVisible() and self.quiz.module_code == self.selected_module:
            return
        if self.quiz is not None:
            self.quiz.close()
            self.quiz.deleteLater()
        from screens.quizzes.module_quiz import ModuleQuiz
        self.quiz = ModuleQuiz(self.selected_module)
        self.quiz.back_requested.connect(self.show_module_choices)
        self._show_screen(self.quiz)

    def shutdown(self):
        self.login.loading.cancel()
        self.register.loading.cancel()
        if hasattr(self, "dashboard") and self.dashboard is not None:
            self.dashboard.loading.cancel()
        if hasattr(self, "main_menu") and self.main_menu is not None:
            self.main_menu.loading.cancel()
        if self.camera_settings is not None:
            self.camera_settings.reject()
        self._dispose_lesson()
        if self.minigames is not None:
            self.minigames.return_menu()
        for screen in (self.quiz, self.module_lessons, self.module_map, self.minigames,
                       self.dashboard._leaderboard, self.dashboard, self.main_menu,
                       self.login, self.register, self.landing, self.welcome):
            if screen is not None:
                screen.close()

    def show_camera_settings(self):
        if auth_service.get_current_user() is None:
            self.show_login()
            return
        if self.camera_settings is not None:
            self.camera_settings.raise_()
            self.camera_settings.activateWindow()
            return
        from screens.camera_setup import CameraSetupDialog
        from backend.camera_service import get_camera_service
        self.camera_settings = CameraSetupDialog(self.main_menu, onboarding=not get_camera_service().configured)

        def finished(result):
            dialog, self.camera_settings = self.camera_settings, None
            if dialog is not None:
                dialog.deleteLater()
        self.camera_settings.finished.connect(finished)
        self.camera_settings.open()

    def open_module_game(self, kind):
        if auth_service.get_current_user() is None:
            self.show_login()
            return
        if self.selected_module is None:
            self.show_module_map()
            return
        if self.minigames is not None and self.minigames.isVisible() and self.minigames.game is not None:
            return
        screen = self._minigame_screen()
        screen.open_game(kind, scope="module", module_code=self.selected_module)
        self._show_screen(screen)

    def back_from_minigames(self):
        if self.minigames.scope == "global":
            self.show_main_menu()
        else:
            self.show_module_choices(self.minigames.module_code)
