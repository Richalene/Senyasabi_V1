from screens.auth.login import LoginScreen
from screens.auth.register import RegisterScreen
from screens.dashboard.dashboard import DashboardWindow


class AppController:
    def __init__(self):
        self.login = LoginScreen()
        self.register = RegisterScreen()
        self.dashboard = DashboardWindow()

        self.login.continue_requested.connect(self.show_dashboard)
        self.login.register_requested.connect(self.show_register)
        self.register.sign_in_requested.connect(self.show_login)
        self.register.create_account_requested.connect(self.show_login)

    def show_login(self):
        self.register.hide()
        self.dashboard.hide()
        self.login.show()

    def show_register(self):
        self.login.hide()
        self.register.show()

    def show_dashboard(self):
        self.login.hide()
        self.register.hide()
        self.dashboard.show()
