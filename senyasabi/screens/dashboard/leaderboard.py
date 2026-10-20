"""Controller for the leaderboard screen."""
from pathlib import Path
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QFontDatabase, QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLayout, QPushButton, QWidget

from backend import auth_service, leaderboard_service
from screens.loading import LoadingOverlay
from screens.navigation import BackButton, SenyaSabiHeader, install_page_menu
from screens.startup import FittedForm
from ui.generated.leaderboard_ui import Ui_Leaderboard


LEADERBOARD_QSS = """
QScrollArea#leaderboardScrollArea,
QScrollArea#leaderboardScrollArea > QWidget,
QWidget#leaderboardContainer {
    background: transparent;
    border: none;
}

QFrame#leaderboardEntry {
    background-color: #D8D8D8;
    border: none;
    border-radius: 46px;
    min-height: 92px;
    max-height: 92px;
}

QFrame#leaderboardEntry[class="leaderboardRank1"] {
    background-color: #FFC646;
}

QFrame#leaderboardEntry[class="leaderboardRank2"] {
    background-color: #F9E6BD;
}

QFrame#leaderboardEntry[class="leaderboardRank3"] {
    background-color: #C9A657;
}

QFrame#leaderboardEntry[class="leaderboardNormal"] {
    background-color: #D8D8D8;
}

QLabel {
    background: transparent;
    border: none;
    color: #704833;
    font-family: "Segoe UI", sans-serif;
    font-size: 26px;
    font-style: italic;
    padding: 0px 10px;
}

QLabel[class="leaderboardMedal"] {
    font-family: "Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji", sans-serif;
    font-size: 38px;
    font-style: normal;
    min-width: 70px;
    max-width: 70px;
    padding: 0px;
}

QLabel[class="leaderboardRank"] {
    font-size: 24px;
    font-weight: 700;
    font-style: normal;
    min-width: 70px;
    max-width: 70px;
    padding: 0px;
}

QLabel[currentUser="true"] {
    color: #FFFFFF;
    font-weight: 800;
    font-style: normal;
}

/* Smooth vertical scrollbar */
QScrollBar:vertical {
    background: rgba(0, 0, 0, 0.08);
    width: 14px;
    margin: 8px 2px 8px 2px;
    border-radius: 7px;
}

QScrollBar::handle:vertical {
    background-color: #8C9656;
    border-radius: 7px;
    min-height: 40px;
}

QScrollBar::handle:vertical:hover {
    background-color: #6E783E;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}
"""


class LeaderboardWindow(QWidget):
    back_requested = Signal()
    menu_requested = Signal()
    _scores_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Leaderboard()
        self.ui.setupUi(self)

        root = Path(__file__).resolve().parents[2]

        # Register custom font
        font_path = root / "resources/font/CherryBombOne-Regular.ttf"
        if font_path.is_file():
            QFontDatabase.addApplicationFont(str(font_path))

        # Explicitly assign backgrounds and images
        gen_bg_pixmap = QPixmap(str(root / "resources/img/gen_bg.png"))
        if not gen_bg_pixmap.isNull():
            self.ui.imageBg.setPixmap(gen_bg_pixmap)
            self.ui.imageBg.setScaledContents(True)

        # Cloud background
        cloud_pixmap = QPixmap(str(root / "resources/img/ui/cloud.png"))
        if not cloud_pixmap.isNull():
            self.ui.cloudBg.setPixmap(cloud_pixmap)
            self.ui.cloudBg.setScaledContents(True)

        # Style title label directly with vector font (no image generation)
        self.ui.titleLabel.setStyleSheet(
            "QLabel#titleLabel { color: #6A5037; font-family: 'Cherry Bomb One'; font-size: 52px; background: transparent; }"
        )

        # Cache medal pixmaps
        self._medals = {
            1: QPixmap(str(root / "resources/img/ui/medal_gold.png")),
            2: QPixmap(str(root / "resources/img/ui/medal_silver.png")),
            3: QPixmap(str(root / "resources/img/ui/medal_bronze.png")),
        }

        # Back button
        self.ui.btnBack.setGeometry(1760, 150, 74, 74)
        self.ui.btnBack = BackButton.replace(self.ui.btnBack)
        self.ui.btnBack.clicked.connect(self.back_requested.emit)

        # Header with streak and hamburger menu
        self.header = SenyaSabiHeader(self)
        self.header.anchor_to_canvas(self.size())
        install_page_menu(self, header=self.header)
        self.ui.lblCurrentStreak = self.header.streak_label
        self.ui.btnMenu = self.header.menu_button

        self.ui.scrollLeaderboard.setObjectName("leaderboardScrollArea")
        self.ui.scrollLeaderboard.setStyleSheet(LEADERBOARD_QSS)
        self.ui.leaderboardLayout.setSpacing(16)
        self.ui.leaderboardLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.ui.leaderboardLayout.setSizeConstraint(QLayout.SizeConstraint.SetMinAndMaxSize)
        self.ui.scrollLeaderboard.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._displayed_user_id = object()
        self._loading_user_id = None
        self._render_entries([])
        self.board_code = "all_time"
        self._scores_changed.connect(self._on_scores_changed)
        self._notify = self._scores_changed.emit
        leaderboard_service.add_scores_listener(self._notify)
        self.destroyed.connect(lambda *_, n=self._notify: leaderboard_service.remove_scores_listener(n))
        self._fitted_form = FittedForm(self)
        self.loading = LoadingOverlay(self)

    def refresh(self):
        user = auth_service.get_current_user() or {}
        user_id = user.get("user_id")
        if self.loading.busy:
            if self._loading_user_id == user_id:
                return False
            self.loading.cancel()
        if self._displayed_user_id != user_id:
            self._render_entries([])
            self._displayed_user_id = user_id
        self._loading_user_id = user_id
        board_code = self.board_code

        def current_session():
            current = auth_service.get_current_user() or {}
            return current.get("user_id") == user_id

        def ready(entries):
            if current_session():
                self._render_entries(entries)

        def failed(error):
            if current_session():
                self._render_entries([], failed=True)

        return self.loading.run(
            lambda: leaderboard_service.get_leaderboard(user_id=user_id, board_code=board_code), ready, failed,
            message="Loading the leaderboard…")

    def _render_entries(self, entries, *, failed=False):
        layout = self.ui.leaderboardLayout
        while layout.count():
            widget = layout.takeAt(0).widget()
            if widget is not None:
                widget.hide()
                widget.deleteLater()
        if hasattr(self, "ui") and hasattr(self.ui, "lblCurrentStreak") and self.ui.lblCurrentStreak:
            self.ui.lblCurrentStreak.setText("0 Days")

        if failed:
            layout.addWidget(QLabel("We couldn't load the leaderboard. Please try again.",
                                   self.ui.leaderboardContainer))
            retry = QPushButton("Retry", self.ui.leaderboardContainer)
            retry.setCursor(Qt.CursorShape.PointingHandCursor)
            retry.setStyleSheet("QPushButton { background: #f7f7dc; color: #526021; border: 1px solid #a9bd43; border-radius: 12px; padding: 8px 18px; font-size: 18px; }")
            retry.clicked.connect(self.refresh)
            layout.addWidget(retry)
            return

        for entry in entries:
            rank = entry["rank_position"]
            current = entry["is_current_user"]
            row = QFrame(self.ui.leaderboardContainer)
            row.setObjectName("leaderboardEntry")
            row.setProperty("class", f"leaderboardRank{rank}" if rank in (1, 2, 3) else "leaderboardNormal")
            row.setProperty("user_id", entry["user_id"])
            row.setProperty("rank_position", rank)
            row.setProperty("currentUser", current)

            columns = QHBoxLayout(row)
            columns.setContentsMargins(40, 12, 48, 12)
            columns.setSpacing(24)

            # Medal / Rank column with emojis
            rank_label = QLabel(row)
            rank_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            medal_emojis = {1: "\U0001F947", 2: "\U0001F948", 3: "\U0001F949"}  # 🥇, 🥈, 🥉
            if rank in medal_emojis:
                rank_label.setText(medal_emojis[rank])
                rank_label.setProperty("class", "leaderboardMedal")
            else:
                rank_label.setText(str(rank))
                rank_label.setProperty("class", "leaderboardRank")
            rank_label.setProperty("currentUser", current)
            columns.addWidget(rank_label)

            # Username column
            name_label = QLabel("YOU" if current else entry["username"], row)
            name_label.setObjectName("username")
            name_label.setProperty("currentUser", current)
            name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            name_label.setToolTip(entry["username"])
            columns.addWidget(name_label, 1)

            # Streak column ("Streak 284")
            streak_val = entry.get("current_streak", 0)
            streak_label = QLabel(f"Streak {streak_val}", row)
            streak_label.setObjectName("streak")
            streak_label.setProperty("currentUser", current)
            streak_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            streak_label.setFixedWidth(240)
            columns.addWidget(streak_label)

            # Badges column ("Badges: 18/20")
            badges_val = entry.get("badges_unlocked", 0)
            badges_label = QLabel(f"Badges: {badges_val}/20", row)
            badges_label.setObjectName("badges")
            badges_label.setProperty("currentUser", current)
            badges_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            badges_label.setFixedWidth(260)
            columns.addWidget(badges_label)

            layout.addWidget(row)
            if current and self.ui.lblCurrentStreak:
                self.ui.lblCurrentStreak.setText(f"{streak_val} Days")

        if not entries:
            empty_label = QLabel("No leaderboard entries yet.", self.ui.leaderboardContainer)
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(empty_label)

    def set_board(self, board_code):
        if board_code not in leaderboard_service.BOARD_CODES:
            raise ValueError(board_code)
        self.board_code = board_code
        return self.refresh()

    def _on_scores_changed(self):
        if self.isVisible():
            self.refresh()

    def showEvent(self, event):
        self.refresh()
        super().showEvent(event)

    def hideEvent(self, event):
        self.loading.cancel()
        super().hideEvent(event)

    def closeEvent(self, event):
        self.loading.cancel()
        super().closeEvent(event)
