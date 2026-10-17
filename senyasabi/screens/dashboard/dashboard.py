# This Python file uses the following encoding: utf-8
import sys

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QMessageBox, QPushButton, QWidget

from screens.loading import LoadingOverlay
from screens.navigation import BackButton, SenyaSabiHeader, install_page_menu
from screens.startup import FittedForm
from ui.generated.ui_form import Ui_main
from ui.generated.dashboard_ui import Ui_Dashboard
from backend import auth_service, dashboard_service


class _DataStatus(QWidget):
    """A small recovery action that does not replace the dashboard's content."""
    def __init__(self, parent, retry, geometry):
        super().__init__(parent)
        self.setGeometry(*geometry)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        self.message = QLabel("We couldn't load your statistics.", self)
        self.message.setStyleSheet("color: #754b3b; background: transparent; font-size: 15px;")
        self.retry = QPushButton("Retry", self)
        self.retry.setCursor(Qt.CursorShape.PointingHandCursor)
        self.retry.setStyleSheet("QPushButton { background: #f7f7dc; color: #526021; border: 1px solid #a9bd43; border-radius: 12px; padding: 6px 18px; }")
        self.retry.clicked.connect(retry)
        row.addWidget(self.message)
        row.addWidget(self.retry)
        row.addStretch()
        self.hide()


def _session_user_id():
    user = auth_service.get_current_user()
    return user.get("user_id") if user else None


class StatisticsDashboardWindow(QWidget):
    """Statistics view; all dashboard data comes through dashboard_service."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Dashboard()
        self.ui.setupUi(self)
        self.ui.titlePanel.resize(300, 60)
        self.ui.btnBack.setGeometry(1280, 150, 110, 42)
        self.ui.btnBack = BackButton.replace(self.ui.btnBack)
        self.ui.streakPanel.hide()
        self.ui.lblCurrentStreak.setObjectName("replacedCurrentStreak")
        self.ui.btnMenu.hide()
        self.ui.btnMenu.setEnabled(False)
        self.ui.btnMenu.setObjectName("replacedMenu")
        self.header = SenyaSabiHeader(self)
        self.header.anchor_to_canvas(self.size())
        install_page_menu(self, header=self.header)
        self.ui.lblCurrentStreak = self.header.streak_label
        self.ui.btnMenu = self.header.menu_button
        self.ui.lblCurrentStreak.setObjectName("lblCurrentStreak")
        self.ui.btnMenu.setObjectName("btnMenu")
        self.ui.badgeCard.resize(240, 180)
        self.ui.badgeTitle.setGeometry(9, 67, 220, 24)
        self.ui.lblLatestBadge.setGeometry(9, 100, 220, 60)
        self.ui.lblLatestBadge.setWordWrap(True)
        icons = {'quizImage': '?', 'lessonsImage': 'Aa', 'modulesImage': '10',
                 'leaderboardImage': '1', 'minigamesImage': 'Play', 'badgeImage': '★'}
        for name, text in icons.items():
            label = getattr(self.ui, name)
            label.setText(text)
            label.setToolTip('')
        self.ui.imgStatsChart.setText('Your progress will appear here as you complete learning activities.')
        self.ui.imgStatsChart.setWordWrap(True)
        for name in ('legendDot1', 'legendDot2', 'legendDot3', 'legendDot4', 'legendDot5', 'legendDot6'):
            getattr(self.ui, name).hide()
        self._menu = None
        self._leaderboard = None
        self.ui.btnBack.clicked.connect(self._open_menu)
        self.ui.btnLeaderboard.clicked.connect(self._open_leaderboard)
        self.data_status = _DataStatus(self, self.refresh_stats, (380, 176, 800, 38))
        self._displayed_user_id = object()
        self._loading_user_id = None
        self._render_stats(dashboard_service.DefaultDashboardRepository().get_dashboard_stats(None))
        self._fitted_form = FittedForm(self)
        self.loading = LoadingOverlay(self)

    def refresh_stats(self):
        user_id = _session_user_id()
        if self.loading.busy:
            if self._loading_user_id == user_id:
                return False
            self.loading.cancel()
        if self._displayed_user_id != user_id:
            self._render_stats(dashboard_service.DefaultDashboardRepository().get_dashboard_stats(None))
            self._displayed_user_id = user_id
        self._loading_user_id = user_id
        self.data_status.hide()

        def ready(data):
            if _session_user_id() == user_id:
                self._render_stats(data)

        def failed(error):
            if _session_user_id() == user_id:
                self.data_status.show()

        return self.loading.run(
            lambda: dashboard_service.get_dashboard_stats(user_id), ready, failed,
            message="Loading your statistics…", controls=(self.data_status.retry,))

    def _render_stats(self, data):
        stats = data["user_statistics"]
        self.ui.lblCurrentStreak.setText(f'{data["streaks"]["current_streak"]} Days')
        self.ui.lblLessonsCompleted.setText(str(stats["lessons_completed"]))
        self.ui.lblTotalQuizScore.setText(str(stats["total_quiz_score"]))
        self.ui.lblModuleCount.setText(str(data["module_count"]))
        badges = data["user_badges"]
        latest = max(badges, key=lambda badge: badge["unlocked_at"]) if badges else None
        self.ui.lblLatestBadge.setText(str(latest["badge_id"]) if latest else "No badges yet")
        self.ui.lblMinigamesCompleted.setText(str(stats["minigames_completed"]))
        rank = data["leaderboard"]["rank_position"]
        self.ui.lblLeaderboardRank.setText(f"#{rank}" if rank else "Unranked")

    def showEvent(self, event):
        self.refresh_stats()
        super().showEvent(event)

    def hideEvent(self, event):
        self.loading.cancel()
        super().hideEvent(event)

    def _open_menu(self):
        if auth_service.get_current_user() is None:
            return
        if self._menu is None:
            self._menu = DashboardWindow()
        self._menu.show()
        self.hide()

    def _open_leaderboard(self):
        if auth_service.get_current_user() is None:
            return
        if self._leaderboard is None:
            from screens.dashboard.leaderboard import LeaderboardWindow
            self._leaderboard = LeaderboardWindow()
            self._leaderboard.back_requested.connect(self._back_from_leaderboard)
            self._leaderboard.menu_requested.connect(self._menu_from_leaderboard)
        self._leaderboard.show()
        self.hide()

    def _back_from_leaderboard(self):
        self._leaderboard.hide()
        self.show()

    def _menu_from_leaderboard(self):
        self._leaderboard.hide()
        self._open_menu()

    def closeEvent(self, event):
        self.loading.cancel()
        if self._leaderboard is not None:
            self._leaderboard.close()
        if self._menu is not None:
            self._menu.close()
        super().closeEvent(event)


class DashboardWindow(QWidget):
    stats_requested = Signal()
    logout_requested = Signal()
    camera_settings_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._alphabet_menu = None
        self._lesson_select = None
        self._learn_window = None
        self._spell_cat = None
        self._spell_words = None
        self._spell_lesson = None
        self._word_menu = None
        self._word_lesson = None
        self._closing = False

        self.ui = Ui_main()
        self.ui.setupUi(self)
        self.ui.streakCard.hide()
        self.ui.streakValue.setObjectName("replacedStreakValue")
        self.ui.btnHamburger.hide()
        self.ui.btnHamburger.setEnabled(False)
        self.ui.btnHamburger.setObjectName("replacedHamburger")
        self.header = SenyaSabiHeader(self)
        self.header.anchor_to_canvas(self.size())
        install_page_menu(self, header=self.header)
        self.ui.streakValue = self.header.streak_label
        self.ui.btnHamburger = self.header.menu_button
        self.ui.streakValue.setObjectName("streakValue")
        self.ui.btnHamburger.setObjectName("btnHamburger")
        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self._shutdown_resources)

        for label in self.findChildren(QLabel):
            label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            label.setTextFormat(Qt.TextFormat.PlainText)
        self.ui.welcomeLabel.setWordWrap(True)
        self.ui.lblLatestBadgeValue.setWordWrap(True)

        self.ui.btnStartLearning.clicked.connect(self._open_lesson_select)
        self.ui.btnMinigames.clicked.connect(self._show_minigames_notice)
        for button in (
            self.ui.btnLessonsCompleted,
            self.ui.btnModule,
            self.ui.btnLatestBadge,
            self.ui.btnLeaderboardRank,
        ):
            button.clicked.connect(self.stats_requested.emit)

        self.logout_menu = self.header.menu_button.menu()
        self.camera_action = self.logout_menu.camera_action
        self.camera_action.triggered.connect(self.camera_settings_requested.emit)
        self.logout_action = self.logout_menu.sign_out_action
        self.logout_action.triggered.connect(self.logout_requested.emit)
        self.data_status = _DataStatus(self, self.refresh_home_stats, (50, 142, 850, 36))
        self._displayed_user_id = object()
        self._loading_user_id = None
        self._render_home_stats(dashboard_service.DefaultDashboardRepository().get_dashboard_stats(None))
        self._fitted_form = FittedForm(self)
        self.loading = LoadingOverlay(self)

    def refresh_home_stats(self):
        user = auth_service.get_current_user() or {}
        user_id = user.get("user_id")
        display_name = user.get("display_name") or user.get("username") or "Learner"
        self.ui.welcomeLabel.setText(f"Welcome Back, {display_name}!")
        if self.loading.busy:
            if self._loading_user_id == user_id:
                return False
            self.loading.cancel()
        if self._displayed_user_id != user_id:
            self._render_home_stats(dashboard_service.DefaultDashboardRepository().get_dashboard_stats(None))
            self._displayed_user_id = user_id
        self._loading_user_id = user_id
        self.data_status.hide()

        def ready(data):
            if _session_user_id() == user_id:
                self._render_home_stats(data)

        def failed(error):
            if _session_user_id() == user_id:
                self.data_status.show()

        return self.loading.run(
            lambda: dashboard_service.get_dashboard_stats(user_id), ready, failed,
            message="Loading your progress…", controls=(self.data_status.retry,))

    def _render_home_stats(self, data):
        stats = data["user_statistics"]
        badges = data["user_badges"]
        latest_badge = max(badges, key=lambda badge: badge["unlocked_at"]) if badges else None
        rank = data["leaderboard"]["rank_position"]

        self.ui.streakValue.setText(f'{data["streaks"]["current_streak"]} Days')
        self.ui.lblLessonsCompleted.setText(str(stats["lessons_completed"]))
        self.ui.lblModule.setText(str(len(data["module_progress"])))
        self.ui.lblLatestBadgeValue.setText(
            str(latest_badge["badge_id"]) if latest_badge else "No badges yet"
        )
        self.ui.lblLeaderboardRank.setText(f"#{rank}" if rank else "Unranked")

    def showEvent(self, event):
        self.refresh_home_stats()
        super().showEvent(event)

    def hideEvent(self, event):
        self.loading.cancel()
        super().hideEvent(event)

    def _show_minigames_notice(self):
        QMessageBox.information(
            self, "Minigames", "Minigames are not available yet."
        )

    # ══════════════════════════════════════════════════════════════════════
    # ALPHABET navigation
    # ══════════════════════════════════════════════════════════════════════

    def _open_alphabet_menu(self):
        if self._alphabet_menu is None:
            from screens.main_menu.alphabet_menu import AlphabetMenuWidget
            self._alphabet_menu = AlphabetMenuWidget()
            self._alphabet_menu.go_back.connect(self._on_back_to_main)
            self._alphabet_menu.open_learn.connect(self._open_lesson_select)
            self._alphabet_menu.open_spell.connect(self._open_spell_category)
        self.hide()
        self._alphabet_menu.show()

    def _open_lesson_select(self):
        if self._lesson_select is None:
            from screens.main_menu.lesson_select import LessonSelectWidget
            self._lesson_select = LessonSelectWidget()
            self._lesson_select.go_back.connect(self._back_to_alphabet_menu)
            self._lesson_select.lesson_chosen.connect(self._open_learn_lesson)
        if self._alphabet_menu is not None:
            self._alphabet_menu.hide()
        self.hide()
        self._lesson_select.show()

    def _open_learn_lesson(self, lesson_number: int):
        from screens.main_menu.alphabet_menu import LESSON_LETTERS
        from screens.lessons.alphabet.alphabet_lesson import AlphabetLessonWidget
        if self._lesson_select is not None:
            self._lesson_select.hide()
        if self._learn_window is not None:
            self._learn_window.close()
        self._learn_window = AlphabetLessonWidget(
            letters=LESSON_LETTERS[lesson_number],
            lesson_number=lesson_number,
        )
        self._learn_window.lesson_finished.connect(self._back_to_lesson_select)
        self._learn_window.show()

    def _open_spell_category(self):
        if self._spell_cat is None:
            from screens.main_menu.spell_select import SpellCategoryWidget
            self._spell_cat = SpellCategoryWidget()
            self._spell_cat.go_back.connect(self._back_to_alphabet_menu)
            self._spell_cat.category_chosen.connect(self._open_spell_words)
        if self._alphabet_menu is not None:
            self._alphabet_menu.hide()
        self._spell_cat.show()

    def _open_spell_words(self, category: str, words: list):
        from screens.main_menu.spell_select import SpellWordWidget
        if self._spell_words is not None:
            self._spell_words.hide()
            self._spell_words.deleteLater()
        self._spell_words = SpellWordWidget(category=category, words=words)
        self._spell_words.go_back.connect(self._back_to_spell_category)
        self._spell_words.word_chosen.connect(
            lambda word, selected_category=category:
                self._open_spell_lesson(word, selected_category)
        )
        if self._spell_cat is not None:
            self._spell_cat.hide()
        self._spell_words.show()

    def _open_spell_lesson(self, word: str, category: str):
        from screens.lessons.spelling.spell_lesson import SpellLessonWidget
        if self._spell_words is not None:
            self._spell_words.hide()
        if self._spell_lesson is not None:
            self._spell_lesson.close()
        self._spell_lesson = SpellLessonWidget(word=word, category=category)
        self._spell_lesson.lesson_finished.connect(self._back_to_spell_words)
        self._spell_lesson.show()

    # ══════════════════════════════════════════════════════════════════════
    # WORD LESSONS navigation
    # ══════════════════════════════════════════════════════════════════════

    def _open_word_menu(self):
        if self._word_menu is None:
            from screens.main_menu.word_menu import WordMenuWidget
            self._word_menu = WordMenuWidget()
            self._word_menu.go_back.connect(self._on_back_to_main)
            self._word_menu.category_chosen.connect(self._open_word_lesson)
        self.hide()
        self._word_menu.show()

    def _open_word_lesson(self, category: str, words: list):
        from screens.lessons.words.word_lesson import WordLessonWidget
        if self._word_menu is not None:
            self._word_menu.hide()
        if self._word_lesson is not None:
            self._word_lesson.close()
        self._word_lesson = WordLessonWidget(words=words, category=category)
        self._word_lesson.lesson_finished.connect(self._back_to_word_menu)
        self._word_lesson.show()

    # ══════════════════════════════════════════════════════════════════════
    # BACK navigation
    # ══════════════════════════════════════════════════════════════════════

    def _on_back_to_main(self):
        if self._alphabet_menu is not None:
            self._alphabet_menu.hide()
        if self._word_menu is not None:
            self._word_menu.hide()
        self.show()

    def _back_to_alphabet_menu(self):
        if self._lesson_select is not None:
            self._lesson_select.hide()
        if self._spell_cat is not None:
            self._spell_cat.hide()
        if self._alphabet_menu is not None:
            self._alphabet_menu.show()
        else:
            self.show()

    def _back_to_lesson_select(self):
        if self._closing:
            return
        window = self._learn_window
        self._learn_window = None
        if window is not None:
            window.deleteLater()
        if self._lesson_select is not None:
            self._lesson_select.show()

    def _back_to_spell_category(self):
        if self._spell_words is not None:
            self._spell_words.hide()
        if self._spell_cat is not None:
            self._spell_cat.show()

    def _back_to_spell_words(self):
        if self._closing:
            return
        window = self._spell_lesson
        self._spell_lesson = None
        if window is not None:
            window.deleteLater()
        if self._spell_words is not None:
            self._spell_words.show()

    def _back_to_word_menu(self):
        if self._closing:
            return
        window = self._word_lesson
        self._word_lesson = None
        if window is not None:
            window.deleteLater()
        if self._word_menu is not None:
            self._word_menu.show()

    def _shutdown_resources(self):
        if self._closing:
            return
        self._closing = True
        self.loading.cancel()
        for attr in ("_learn_window", "_spell_lesson", "_word_lesson"):
            window = getattr(self, attr)
            if window is not None:
                window.close()
                window.deleteLater()
                setattr(self, attr, None)
        for attr in (
            "_alphabet_menu", "_lesson_select", "_spell_cat",
            "_spell_words", "_word_menu",
        ):
            window = getattr(self, attr)
            if window is not None:
                window.close()

    def closeEvent(self, event: QCloseEvent):
        self._shutdown_resources()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = DashboardWindow()
    widget.show()
    sys.exit(app.exec())
