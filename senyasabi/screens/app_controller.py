import logging
from PySide6.QtWidgets import QLineEdit, QMainWindow, QStackedWidget
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QColor, QPalette

from screens.auth.login import LoginScreen
from screens.auth.register import RegisterScreen
from screens.startup import WelcomeScreen, LandingScreen
from screens.dashboard.dashboard import DashboardWindow, StatisticsDashboardWindow
from screens.loading import LoadingOverlay
from backend import auth_service
from backend.config import PRODUCTION, SUPABASE_URL, SUPABASE_ANON_KEY, CLIENT_MODE
from backend.content_service import get_signs_for_module
from screens.dialogs import ComingSoonDialog
import threading
from PySide6.QtWidgets import QApplication
from screens.camera_permission import ensure_camera_permission

_active_controller = None

def get_active_controller():
    return _active_controller

class MainWindowShell(QMainWindow):
    """Persistent top-level host window managing a QStackedWidget for single-window navigation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SenyaSabi")
        self.setMinimumSize(1024, 576)
        self.resize(1920, 1080)

        # Set default application background palette
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#c5d27b"))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        self.stacked_widget = QStackedWidget(self)
        self.setCentralWidget(self.stacked_widget)

    def closeEvent(self, event):
        controller = get_active_controller()
        if controller is not None:
            controller.shutdown()
        event.accept()

class AppController:
    def __init__(self):
        global _active_controller
        _active_controller = self
        app = QApplication.instance()
        if app is not None:
            app.setProperty("app_controller", self)

        self.shell = MainWindowShell()
        self.stack = self.shell.stacked_widget
        self.loading_overlay = LoadingOverlay(self.shell, cancel_on_hide=False)
        self.loading_overlay.hide()

        self.welcome = WelcomeScreen()
        self.landing = LandingScreen()
        self.login = LoginScreen()
        self.register = RegisterScreen()
        self.dashboard = StatisticsDashboardWindow()
        self.main_menu = DashboardWindow()

        # Mount persistent screens into QStackedWidget
        for persistent_screen in (self.welcome, self.landing, self.login, self.register,
                                  self.main_menu, self.dashboard):
            self.stack.addWidget(persistent_screen)
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

        self.login.continue_requested.connect(self.login_user)
        self.login.register_requested.connect(self.show_register)
        self.login.back_requested.connect(self.show_landing)
        self.register.back_requested.connect(self.show_landing)
        self.register.sign_in_requested.connect(self.show_login)
        self.register.create_account_requested.connect(self.register_user)
        self.welcome.ui.btnContinue.clicked.connect(self.show_landing)
        self.landing.ui.btnGetStarted.clicked.connect(self.show_register)
        self.landing.ui.btnLogin.clicked.connect(self.show_login)

    def _post_login_sync(self, user):
        """Warm the local SQLite caches without blocking the UI. Never fails the login."""
        try:
            from backend import leaderboard_service
            for board in ("all_time", "weekly", "monthly"):
                leaderboard_service.refresh_leaderboard(board)   # already runs on a worker

            def _background_pull():
                try:
                    auth_service.sync_user_info(user["user_id"])
                except Exception:
                    pass
                try:
                    from backend import progress_sync
                    progress_sync.pull_user_progress()
                except Exception as err:
                    logging.getLogger(__name__).warning("Post-login progress pull failed: %s", err)

            threading.Thread(target=_background_pull, daemon=True, name="post-login-sync").start()
        except Exception:
            logging.getLogger(__name__).exception("Post-login sync could not start")

    def _show_screen(self, screen, *args, **kwargs):
        if screen is None:
            return

        # Show brief transition overlay over shell if shell is visible
        if hasattr(self, "loading_overlay") and self.loading_overlay is not None and self.shell.isVisible():
            try:
                self.loading_overlay.setGeometry(self.shell.rect())
                self.loading_overlay.frame = 0
                self.loading_overlay.show()
                self.loading_overlay.raise_()
                self.loading_overlay.animation.start()
                # Clear overlay once the new screen renders
                QTimer.singleShot(150, self._hide_transition_overlay)
            except Exception:
                pass

        # Ensure screen is mounted in the stack
        if self.stack.indexOf(screen) == -1:
            self.stack.addWidget(screen)
        self.stack.setCurrentWidget(screen)
        # Ensure MainWindowShell is presented if not already visible
        if not self.shell.isVisible():
            app = QApplication.instance()
            if hasattr(app, "_present"):
                app._present(self.shell)
            else:
                self.shell.show()

        # Legacy cleanup for any standalone popup screens that were not migrated to stack
        from shiboken6 import isValid
        windows = [getattr(self.dashboard, "_leaderboard", None)]
        windows.extend(getattr(self.main_menu, name, None) for name in (
            "_alphabet_menu", "_lesson_select", "_learn_window", "_spell_cat",
            "_spell_words", "_spell_lesson", "_word_menu", "_word_lesson"))
        for window in windows:
            if window is not None and window is not screen:
                try:
                    if isValid(window) and window.isWindow():
                        window.hide()
                except Exception:
                    pass

    def _hide_transition_overlay(self):
        if hasattr(self, "loading_overlay") and self.loading_overlay is not None:
            try:
                self.loading_overlay.animation.stop()
                self.loading_overlay.hide()
            except Exception:
                pass

    def show_startup_splash(self):
        """Display the animated loading screen as the startup splash before revealing the welcome screen."""
        self._show_screen(self.welcome)
        if hasattr(self, "loading_overlay") and self.loading_overlay is not None:
            try:
                self.loading_overlay.setGeometry(self.shell.rect())
                self.loading_overlay.text.setText("Loading SenyaSabi...")
                self.loading_overlay.frame = 0
                self.loading_overlay.show()
                self.loading_overlay.raise_()
                self.loading_overlay.animation.start()
                # Transition smoothly to the welcome screen after 1400ms
                QTimer.singleShot(1400, self._finish_startup_splash)
            except Exception:
                pass

    def _finish_startup_splash(self):
        if hasattr(self, "loading_overlay") and self.loading_overlay is not None:
            try:
                self.loading_overlay.text.setText("Loading...")
                self.loading_overlay.animation.stop()
                self.loading_overlay.hide()
            except Exception:
                pass

    def show_welcome(self):
        self._show_screen(self.welcome)

    def show_landing(self):
        self._show_screen(self.landing)

    def _show_coming_soon(self):
        dialog = ComingSoonDialog(self)
        dialog.exec()

    def _clear_passwords(self):
        for field in (self.login.password_input, self.register.password_input,
                      getattr(self.register, 'confirm_password_input', None)):
            if field is None:
                continue
            toggle = getattr(field, "visibility_toggle", None)
            if toggle is not None:
                toggle.setChecked(False)
            field.clear()

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
            from backend.score_service import flush_pending_async
            flush_pending_async()          # anything queued while offline last session
            self._post_login_sync(user)
            self.show_main_menu()

        # In distributed mode: Try FastAPI first, fall back to direct Supabase
        # In direct mode: Use direct Supabase
        if CLIENT_MODE == "direct":
            # Direct Supabase authentication
            screen.loading.run(
                lambda: auth_service.authenticate_with_supabase(identifier, password, establish_session=False),
                signed_in, lambda error: self._auth_failed(screen, error, "sign you in"),
                message="Signing you in…", controls=(screen._ui,))
        elif CLIENT_MODE == "distributed":
            screen.loading.run(
                lambda: auth_service.authenticate_user(identifier, password, establish_session=False),
                signed_in, lambda error: self._auth_failed(screen, error, "sign you in"),
                message="Signing you in…", controls=(screen._ui,))

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
                           message="Creating your account…", controls=(screen._ui,))

    def logout(self):
        if getattr(self, "_logging_out", False):
            return
        self._logging_out = True
        try:
            self.login.loading.cancel()
            self.register.loading.cancel()
            if self.camera_settings is not None:
                self.camera_settings.reject()
            self._dispose_lesson()
            if self.minigames is not None:
                self.minigames.return_menu()
            auth_service.logout_user()
            self.selected_module = None
            self.login.email_input.clear()
            self.show_login()
        finally:
            self._logging_out = False
            
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
        try:
            self.dashboard.refresh_stats()
        except Exception:
            pass

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
        elif self.selected_module in ("months", "actions"):
            if self.module_lessons is not None:
                self.module_lessons._on_expression_clicked()
            return
        else:
            from backend.content_service import get_lesson_model_code, get_words_for_lesson, get_words_for_module
            words = get_words_for_lesson(self.selected_module, number)
            model_code = get_lesson_model_code(self.selected_module, number)
            from screens.lessons.words.word_lesson import WordLessonWidget
            screen = WordLessonWidget(words, model_code)
        self.active_lesson = screen
        screen.lesson_finished.connect(self._lesson_back)
        if hasattr(screen, "layout_comp") and hasattr(screen.layout_comp, "results_widget") and screen.layout_comp.results_widget is not None:
            screen.layout_comp.results_widget.next_lesson_requested.connect(
                lambda next_number=number + 1: self._open_next_lesson(next_number)
            )
        # if self.selected_module == "alphabet":
        #     screen.layout_comp.results_widget.next_lesson_requested.connect(
        #         lambda next_number=number + 1: self._open_next_lesson(next_number)
        #     )
        self._show_screen(screen)

    def _open_next_lesson(self, number):
        self._dispose_lesson()
        self.open_module_lesson(number)

    def _dispose_lesson(self):
        screen, self.active_lesson = self.active_lesson, None
        if screen is not None:
            logging.warning("[DIAG] AppController._dispose_lesson: enter (screen=%s)", type(screen).__name__)
            try:
                screen.lesson_finished.disconnect(self._lesson_back)
            except Exception:
                pass
            try:
                from shiboken6 import isValid
                if isValid(screen):
                    logging.warning("[DIAG] AppController._dispose_lesson: before removeWidget / screen.close() / deleteLater()")
                    if hasattr(self, "stack") and self.stack is not None:
                        self.stack.removeWidget(screen)
                    screen.close()
                    screen.deleteLater()
                    logging.warning("[DIAG] AppController._dispose_lesson: after removeWidget / screen.close() / deleteLater()")
            except Exception:
                logging.exception("[DIAG] AppController._dispose_lesson: error")
            logging.warning("[DIAG] AppController._dispose_lesson: exit")

    def _lesson_back(self):
        logging.warning("[DIAG] AppController._lesson_back: enter")
        self._dispose_lesson()
        try:
            self.main_menu.refresh_home_stats()
        except Exception:
            pass
        self.show_module_choices()
        logging.warning("[DIAG] AppController._lesson_back: exit")

    def open_module_quiz(self):
        if auth_service.get_current_user() is None:
            self.show_login()
            return
        if self.selected_module is None:
            self.show_module_map()
            return
        if self.selected_module in ("months", "actions"):
            if self.module_lessons is not None:
                self.module_lessons._on_expression_clicked()
            return
        # Check if the module has signs
        signs = get_signs_for_module(self.selected_module)
        if not signs:
            self._show_coming_soon()
            return
        if self.quiz is not None and self.quiz.isVisible() and self.quiz.module_code == self.selected_module:
            return
        if self.quiz is not None:
            if hasattr(self, "stack") and self.stack is not None:
                self.stack.removeWidget(self.quiz)
            self.quiz.close()
            self.quiz.deleteLater()
            self.quiz = None
        from screens.quizzes.module_quiz import ModuleQuiz
        self.quiz = ModuleQuiz(self.selected_module)
        self.quiz.back_requested.connect(self.show_module_choices)
        self._show_screen(self.quiz)

    def shutdown(self):
        # try:
        #     from backend import camera_ownership
        #     camera_ownership.release_all()
        # except Exception:
        #     pass
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
        if hasattr(self, "shell") and self.shell is not None:
            self.shell.close()

    def show_camera_settings(self):
        if auth_service.get_current_user() is None:
            self.show_login()
            return

        if self.camera_settings is not None:
            self.camera_settings.raise_()
            self.camera_settings.activateWindow()
            return

        def permission_resolved(granted):
            if not granted:
                from PySide6.QtWidgets import QMessageBox

                QMessageBox.warning(
                    self,
                    "Camera Permission Required",
                    "SenyaSabi needs camera access to configure your camera. "
                    "Please enable camera access in macOS System Settings "
                    "under Privacy & Security > Camera."
                )
                return

            # Check again in case the settings window was opened meanwhile.
            if self.camera_settings is not None:
                self.camera_settings.raise_()
                self.camera_settings.activateWindow()
                return

            from screens.camera_setup import CameraSetupDialog
            from backend.camera_service import get_camera_service

            self.camera_settings = CameraSetupDialog(
                self.main_menu,
                onboarding=not get_camera_service().configured
            )

            self.camera_settings.destroyed.connect(
                lambda: setattr(self, "camera_settings", None)
            )

            self.camera_settings.show()

        ensure_camera_permission(permission_resolved)

    def open_module_game(self, kind):
        if auth_service.get_current_user() is None:
            self.show_login()
            return
        if self.selected_module is None:
            self.show_module_map()
            return
        if self.selected_module in ("months", "actions"):
            if self.module_lessons is not None:
                self.module_lessons._on_expression_clicked()
            return
        # Check if the module has signs
        signs = get_signs_for_module(self.selected_module)
        if not signs:
            self._show_coming_soon()
            return
        if self.minigames is not None and self.minigames.isVisible() and self.minigames.game is not None:
            return
        screen = self._minigame_screen()
        screen.open_game(
            kind,
            scope="module",
            module_code=self.selected_module
        )
        self._show_screen(screen)

    def back_from_minigames(self):
        if self.minigames.scope == "global":
            self.show_main_menu()
        else:
            self.show_module_choices(self.minigames.module_code)

    def dev_login(self):
        """Dev login stub for test compatibility.
        
        This was removed for production security but is kept as a stub
        for test compatibility in development mode.
        """
        import logging
        logger = logging.getLogger(__name__)
        if CLIENT_MODE != "fastapi":
            logger.warning("dev_login called in non-fastapi mode - this should not happen")
            return
        
        # In development, authenticate with a test user
        try:
            from backend import auth_service
            user = auth_service.authenticate_user("test@example.com", "testpassword123", establish_session=True)
            if user:
                logger.info("Dev login successful")
            else:
                logger.warning("Dev login failed")
        except Exception as e:
            logger.warning("Dev login error: %s", e)

    def test_connection(self) -> dict:
        """
        Test connection to Supabase and FastAPI backend.
        
        Returns:
            Dict with 'supabase' (bool), 'fastapi' (bool), 'message' (str)
        """
        logger = logging.getLogger(__name__)
        result = {
            "supabase": False,
            "fastapi": False,
            "message": ""
        }
        
        # Test Supabase connection
        if PRODUCTION and SUPABASE_URL and SUPABASE_ANON_KEY:
            try:
                import requests
                # Test Supabase health endpoint
                response = requests.get(f"{SUPABASE_URL}/rest/v1/", 
                                      headers={"apikey": SUPABASE_ANON_KEY},
                                      timeout=5)
                result["supabase"] = response.status_code in (200, 401)  # 401 means server is reachable
                if result["supabase"]:
                    logger.info("Supabase connection test passed")
                else:
                    logger.warning("Supabase connection test failed: %s", response.status_code)
            except requests.exceptions.Timeout:
                logger.warning("Supabase connection test timed out")
                result["message"] = "Supabase connection timed out"
            except requests.exceptions.ConnectionError:
                logger.warning("Supabase connection test failed: connection error")
                result["message"] = "Could not connect to Supabase"
            except Exception as e:
                logger.warning("Supabase connection test error: %s", e)
                result["message"] = f"Supabase connection error: {str(e)}"
        else:
            logger.info("Skipping Supabase connection test (not in production or not configured)")
            result["supabase"] = None  # Not applicable
        
        # Test FastAPI backend connection (if configured)
        try:
            from backend.config import FASTAPI_HOST, FASTAPI_PORT, API_BASE_URL
            import requests
            api_url = API_BASE_URL or f"http://{FASTAPI_HOST}:{FASTAPI_PORT}"
            response = requests.get(f"{api_url}/health", timeout=5)
            result["fastapi"] = response.status_code == 200
            if result["fastapi"]:
                logger.info("FastAPI connection test passed")
            else:
                logger.warning("FastAPI connection test failed: %s", response.status_code)
        except requests.exceptions.Timeout:
            logger.warning("FastAPI connection test timed out")
            if not result["message"]:
                result["message"] = "FastAPI connection timed out"
        except requests.exceptions.ConnectionError:
            logger.warning("FastAPI connection test failed: connection error")
            if not result["message"]:
                result["message"] = "Could not connect to FastAPI backend"
        except Exception as e:
            logger.warning("FastAPI connection test error: %s", e)
            if not result["message"]:
                result["message"] = f"FastAPI connection error: {str(e)}"
        
        # Set overall message if both failed
        if not result["supabase"] and not result["fastapi"] and not result["message"]:
            result["message"] = "Could not connect to any backend service"
        elif result["supabase"] or result["fastapi"]:
            result["message"] = "Connection successful"
        
        return result