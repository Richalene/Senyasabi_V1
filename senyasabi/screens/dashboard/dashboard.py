from pathlib import Path
# This Python file uses the following encoding: utf-8
import sys

import math
import os
from PySide6.QtCore import Qt, Signal, QPointF, QRectF
from PySide6.QtGui import (
    QPixmap, QCloseEvent, QFontDatabase, QPainter,
    QColor, QPen, QBrush, QPolygonF, QFont
)
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QMessageBox, QPushButton, QWidget

from screens.loading import LoadingOverlay
from screens.navigation import BackButton, SenyaSabiHeader, install_page_menu
from screens.startup import FittedForm
from ui.generated.ui_form import Ui_main
from ui.generated.dashboard_ui import Ui_Dashboard
from backend import auth_service, dashboard_service

def _ensure_cherry_bomb_font():
    font_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "resources", "font", "CherryBombOne-Regular.ttf"
    )
    if os.path.exists(font_path):
        QFontDatabase.addApplicationFont(font_path)



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
        _ensure_cherry_bomb_font()
        self.ui = Ui_Dashboard()
        self.ui.setupUi(self)
        root = Path(__file__).resolve().parents[2]
        if hasattr(self.ui, "imageBg"):
            self.ui.imageBg.setPixmap(QPixmap(str(root / "resources/img/ui/dashboard_bg.png")))
            self.ui.imageBg.setScaledContents(True)
        self.ui.titlePanel.hide()
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
        self.ui.lblLatestBadge.setWordWrap(True)
        if hasattr(self.ui, "imgStatsChart"):
            self.ui.imgStatsChart.setGeometry(150, 310, 450, 450)
            self.ui.imgStatsChart.setScaledContents(True)
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
        lp_completed = sum(1 for lp in data.get("lesson_progress", []) if lp.get("status") == "Completed")
        completed_count = max(stats.get("lessons_completed", 0), lp_completed)
        self.ui.lblLessonsCompleted.setText(str(completed_count))
        self.ui.lblTotalQuizScore.setText(str(stats["total_quiz_score"]))
        module_count = len(data["module_progress"]) if data.get("module_progress") else data.get("module_count", 0)
        self.ui.lblModuleCount.setText(str(module_count))
        self.ui.modulesImage.setText(str(module_count))
        badges = data["user_badges"]
        latest = max(badges, key=lambda badge: badge["unlocked_at"]) if badges else None
        named = data.get("latest_badge") or {}
        self.ui.lblLatestBadge.setText(named.get("badge_name") or (str(latest["badge_id"]) if latest else "No badges yet"))
        self.ui.lblMinigamesCompleted.setText(str(stats["minigames_completed"]))
        rank = data["leaderboard"]["rank_position"]
        self.ui.lblLeaderboardRank.setText(f"#{rank}" if rank else "Unranked")
        chart_pix = self._draw_spider_chart(data.get("module_performance", []), data.get("lesson_progress", []))
        if hasattr(self.ui, "imgStatsChart") and chart_pix is not None:
            self.ui.imgStatsChart.setPixmap(chart_pix)

    def _draw_spider_chart(self, module_perf_list, lesson_progress_list=None):
        """Draw 6-axis performance spider chart across the core modules."""
        width, height = 450, 450
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        cx = width / 2.0
        cy = height / 2.0
        max_radius = min(cx, cy) - 58.0

        # Clockwise 6 core modules starting from 12 o'clock
        CORE_MODULES = [
            ("alphabet", "Module 1"),
            ("greeting", "Module 2"),
            ("survival", "Module 3"),
            ("number", "Module 4"),
            ("days", "Module 5"),
            ("family", "Module 6"),
        ]
        num_axes = len(CORE_MODULES)
        angles = [-math.pi / 2.0 + i * (2.0 * math.pi / num_axes) for i in range(num_axes)]

        perf_by_code = {p.get("module_code", "").lower(): p for p in (module_perf_list or [])}

        # Calculate module lesson completion percentage as baseline
        completed_lessons = set()
        for lp in (lesson_progress_list or []):
            if lp.get("status") == "Completed":
                completed_lessons.add(lp.get("lesson_id"))

        # Fallback completion map by checking completed lessons count
        fallback_scores = {}
        if completed_lessons:
            try:
                from backend import content_service
                for code, _ in CORE_MODULES:
                    lessons = content_service.list_lessons_for_module(code)
                    if lessons:
                        cnt = sum(1 for les in lessons if getattr(les, "lesson_id", None) in completed_lessons)
                        fallback_scores[code] = round((cnt / len(lessons)) * 100.0, 1)
            except Exception:
                pass

        axes_scores = []
        for code, title in CORE_MODULES:
            perf = perf_by_code.get(code, {})
            score = float(perf.get("score") or 0.0)
            if score <= 0.0 and code in fallback_scores:
                score = float(fallback_scores[code])
            axes_scores.append((title, score))

        # 1. Concentric web levels (20%, 40%, 60%, 80%, 100%)
        levels = [0.2, 0.4, 0.6, 0.8, 1.0]
        for lvl in levels:
            poly = QPolygonF()
            r = max_radius * lvl
            for angle in angles:
                poly.append(QPointF(cx + r * math.cos(angle), cy + r * math.sin(angle)))
            pen = QPen(QColor(160, 180, 110, 150 if lvl == 1.0 else 85))
            pen.setWidthF(2.0 if lvl == 1.0 else 1.2)
            painter.setPen(pen)
            painter.setBrush(QBrush(QColor(255, 255, 255, 35 if lvl == 1.0 else 0)))
            painter.drawPolygon(poly)

        # 2. Radial spokes
        spoke_pen = QPen(QColor(140, 160, 90, 120))
        spoke_pen.setWidthF(1.5)
        painter.setPen(spoke_pen)
        for angle in angles:
            painter.drawLine(
                QPointF(cx, cy),
                QPointF(cx + max_radius * math.cos(angle), cy + max_radius * math.sin(angle))
            )

        # 3. Data polygon
        data_poly = QPolygonF()
        has_any_score = any(score > 0 for _, score in axes_scores)
        for i, (_, score) in enumerate(axes_scores):
            capped = max(0.0, min(100.0, score))
            r = max_radius * (capped / 100.0)
            data_poly.append(QPointF(cx + r * math.cos(angles[i]), cy + r * math.sin(angles[i])))

        if has_any_score:
            fill_brush = QBrush(QColor(220, 60, 50, 125))
            painter.setBrush(fill_brush)
            data_pen = QPen(QColor(200, 40, 30, 230))
            data_pen.setWidthF(2.8)
            painter.setPen(data_pen)
            painter.drawPolygon(data_poly)

        # 4. Markers and labels
        point_brush = QBrush(QColor(255, 255, 255))
        point_pen = QPen(QColor(180, 30, 20) if has_any_score else QColor(140, 160, 90))
        point_pen.setWidthF(2.5)

        font = QFont("Segoe UI", 11, QFont.Weight.Bold)
        painter.setFont(font)

        for i, (title, score) in enumerate(axes_scores):
            capped = max(0.0, min(100.0, score))
            r = max_radius * (capped / 100.0)
            pt = QPointF(cx + r * math.cos(angles[i]), cy + r * math.sin(angles[i]))

            painter.setPen(point_pen)
            painter.setBrush(point_brush)
            painter.drawEllipse(pt, 4.5, 4.5)

            # Axis outer text
            label_r = max_radius + 30.0
            lx = cx + label_r * math.cos(angles[i])
            ly = cy + label_r * math.sin(angles[i])

            score_str = f"{int(capped)}%" if capped > 0 else "0%"
            full_text = f"{title}\n{score_str}"

            label_w, label_h = 110, 40
            label_rect = QRectF(lx - label_w / 2.0, ly - label_h / 2.0, label_w, label_h)
            painter.setPen(QColor(92, 59, 40))
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, full_text)

        painter.end()
        return pixmap


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

        _ensure_cherry_bomb_font()
        self.ui = Ui_main()
        self.ui.setupUi(self)
        root = Path(__file__).resolve().parents[2]
        if hasattr(self.ui, "imageBg"):
            self.ui.imageBg.setPixmap(QPixmap(str(root / "resources/img/home_bg.png")))
            self.ui.imageBg.setScaledContents(True)
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
        module_count = len(data["module_progress"]) if data.get("module_progress") else data.get("module_count", 0)

        self.ui.streakValue.setText(f'{data["streaks"]["current_streak"]} Days')
        lp_completed = sum(1 for lp in data.get("lesson_progress", []) if lp.get("status") == "Completed")
        completed_count = max(stats.get("lessons_completed", 0), lp_completed)
        self.ui.lblLessonsCompleted.setText(str(completed_count))
        self.ui.lblModule.setText(str(module_count))
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

    def closeEvent(self, event):
        self.loading.cancel()
        super().closeEvent(event)

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
        if category.casefold() == "alphabet":
            self._open_lesson_select()
            return
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
