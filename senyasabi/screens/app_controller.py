from screens.auth.login import LoginScreen
from screens.auth.register import RegisterScreen
from screens.startup import WelcomeScreen, LandingScreen
from screens.dashboard.dashboard import DashboardWindow, StatisticsDashboardWindow
from backend import auth_service
from PySide6.QtWidgets import QPushButton


class AppController:
    def __init__(self):
        self.welcome = WelcomeScreen()
        self.landing = LandingScreen()
        self.login = LoginScreen()
        self.register = RegisterScreen()
        self.dashboard = StatisticsDashboardWindow()
        self.main_menu = DashboardWindow()
        self.dashboard._menu = self.main_menu
        self.dashboard.ui.btnBack.clicked.disconnect()
        self.dashboard.ui.btnMenu.clicked.disconnect()
        self.dashboard.ui.btnBack.clicked.connect(self.show_main_menu)
        self.dashboard.ui.btnMenu.clicked.connect(self.show_main_menu)
        self.dashboard_button = QPushButton("Dashboard", self.main_menu)
        self.dashboard_button.setObjectName("btnDashboard")
        self.dashboard_button.setGeometry(1020, 20, 120, 36)
        self.dashboard_button.clicked.connect(self.show_dashboard)

        self.logout_button = QPushButton("Log out", self.main_menu)
        self.logout_button.setObjectName("logoutButton")
        self.logout_button.setGeometry(1160, 20, 120, 36)
        self.logout_button.clicked.connect(self.logout)

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
                   self.main_menu, self.dashboard, self.dashboard._leaderboard]
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
