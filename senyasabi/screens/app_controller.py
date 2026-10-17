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
        self.selected_module = None
        self.main_menu.ui.btnStartLearning.clicked.disconnect()
        self.main_menu.ui.btnStartLearning.clicked.connect(self.show_module_map)
        self.main_menu.ui.btnMinigames.clicked.disconnect()
        self.main_menu.ui.btnMinigames.clicked.connect(self.show_minigames)
        self.dashboard._menu = self.main_menu
        self.dashboard.ui.btnBack.clicked.disconnect()
        self.dashboard.ui.btnMenu.clicked.disconnect()
        self.dashboard.ui.btnBack.clicked.connect(self.show_main_menu)
        self.dashboard.ui.btnMenu.clicked.connect(self.show_main_menu)
        self.main_menu.stats_requested.connect(self.show_dashboard)
        self.main_menu.logout_requested.connect(self.logout)

        self.login.dev_login_requested.connect(self.dev_login)
        self.register.dev_login_requested.connect(self.dev_login)
        self.login.continue_requested.connect(self.login_user)
        self.login.register_requested.connect(self.show_register)
        self.register.sign_in_requested.connect(self.show_login)
        self.register.create_account_requested.connect(self.register_user)
        self.welcome.ui.btnContinue.clicked.connect(self.show_landing)
        self.landing.ui.btnGetStarted.clicked.connect(self.show_register)
        self.landing.ui.btnLogin.clicked.connect(self.show_login)

    def _show_screen(self, screen):
        # Reuse each screen and show the destination before hiding the source.
        screen.show()
        windows = [self.welcome, self.landing, self.login, self.register,
                   self.main_menu, self.dashboard, self.dashboard._leaderboard, self.minigames, self.module_map, self.module_lessons]
        windows.extend(getattr(self.main_menu, name) for name in (
            "_alphabet_menu", "_lesson_select", "_learn_window", "_spell_cat",
            "_spell_words", "_spell_lesson", "_word_menu", "_word_lesson"))
        for window in windows:
            if window is None:
                continue
            if window is not screen:
                window.hide()

    def show_welcome(self):
        self._show_screen(self.welcome)

    def show_landing(self):
        self._show_screen(self.landing)

    def _clear_passwords(self):
        self.login.password_input.clear()
        self.register.password_input.clear()
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
        try:
            auth_service.authenticate_user(
                self.login.email_input.text(), self.login.password_input.text())
        except auth_service.AuthError as error:
            self.login.error_label.setText(str(error))
        else:
            self.show_main_menu()
        finally:
            self._clear_passwords()

    def register_user(self):
        try:
            if self.register.password_input.text() != self.register.confirm_password_input.text():
                raise auth_service.AuthError("Passwords do not match.")
            user = auth_service.register_user(
                self.register.username_input.text(), self.register.email_input.text(),
                self.register.password_input.text(), self.register.name_input.text())
        except auth_service.AuthError as error:
            self.register.error_label.setText(str(error))
        else:
            self.login.email_input.setText(user["username"])
            self.show_login()
            self.login.error_label.setText("Account created. Sign in to continue.")
            for field in (self.register.username_input, self.register.email_input,
                          self.register.name_input):
                field.clear()
        finally:
            self._clear_passwords()

    def logout(self):
        auth_service.logout_user()
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
        if self.minigames is None:
            from screens.minigames.minigame_select import MinigameSelect
            self.minigames = MinigameSelect()
            self.minigames.back_requested.connect(self.back_from_minigames)
        self.minigames.module_code = None
        self._show_screen(self.minigames)

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
        else:
            self.module_lessons.set_module(self.selected_module)
        self.module_lessons.set_streak(self.main_menu.ui.streakValue.text())
        self._show_screen(self.module_lessons)

    def open_module_lesson(self, number):
        if auth_service.get_current_user() is None:
            self.show_login()
            return
        if self.selected_module == "alphabet":
            self.main_menu._open_learn_lesson(number)
            screen = self.main_menu._learn_window
        else:
            from screens.main_menu.word_menu import _load_categories
            code = self.selected_module.upper()
            self.main_menu._open_word_lesson(code, _load_categories()[code])
            screen = self.main_menu._word_lesson
        screen.lesson_finished.disconnect()
        screen.lesson_finished.connect(self.show_module_choices)
        self._show_screen(screen)

    def open_module_game(self, kind):
        if auth_service.get_current_user() is None:
            self.show_login()
            return
        if self.minigames is None:
            from screens.minigames.minigame_select import MinigameSelect
            self.minigames = MinigameSelect()
            self.minigames.back_requested.connect(self.back_from_minigames)
        self.minigames.open_game(kind, module_code=self.selected_module)
        self._show_screen(self.minigames)

    def back_from_minigames(self):
        if self.minigames.module_code is None:
            self.show_main_menu()
        else:
            self.show_module_choices(self.minigames.module_code)
