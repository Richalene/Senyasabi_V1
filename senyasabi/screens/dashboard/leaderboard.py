"""Controller for the existing leaderboard.ui form."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLayout, QPushButton, QWidget

from backend import auth_service, leaderboard_service
from screens.loading import LoadingOverlay
from screens.navigation import BackButton, SenyaSabiHeader, install_page_menu
from screens.startup import FittedForm
from ui.generated.leaderboard_ui import Ui_Leaderboard


# Based on the supplied leaderboard QSS; scoped to the scrolling list.
LEADERBOARD_QSS = """
QScrollArea#leaderboardScrollArea,
QScrollArea#leaderboardScrollArea > QWidget,
QWidget#leaderboardContainer {
    background: transparent; border: none;
}
QFrame#leaderboardEntry {
    background-color: #F1F1F1; border: none; border-radius: 28px;
    min-height: 58px; max-height: 58px;
}
QFrame#leaderboardEntry[class="leaderboardRank1"] { background-color: #FFC548; }
QFrame#leaderboardEntry[class="leaderboardRank2"] { background-color: #F7E6B9; }
QFrame#leaderboardEntry[class="leaderboardRank3"] { background-color: #BC8C55; }
QFrame#leaderboardEntry[class="leaderboardNormal"] { background-color: #F1F1F1; }
QFrame#leaderboardEntry[class="leaderboardCurrentUser"] { background-color: #CDAA55; }
QLabel {
    background: transparent; border: none; color: #754B3B;
    font-size: 15px; font-style: italic; padding: 0px 8px;
}
QLabel[class="leaderboardMedal"] {
    font-family: "Segoe UI Emoji"; font-size: 25px; font-style: normal;
    min-width: 46px; max-width: 46px; padding: 0px;
}
QLabel[class="leaderboardRank"] {
    font-size: 16px; font-weight: 700; font-style: normal;
    min-width: 46px; max-width: 46px; padding: 0px;
}
QLabel[currentUser="true"] {
    color: #38451F; font-weight: 700; font-style: normal;
}
QScrollBar:vertical {
    background: transparent; width: 10px; margin: 4px 1px 4px 1px;
}
QScrollBar::handle:vertical {
    background-color: #A9BD43; border-radius: 5px; min-height: 30px;
}
QScrollBar::handle:vertical:hover { background-color: #8FA52E; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
"""


class LeaderboardWindow(QWidget):
    back_requested = Signal()
    menu_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Leaderboard()
        self.ui.setupUi(self)
        self.ui.btnBack.setGeometry(1110, 125, 100, 36)
        self.ui.btnBack = BackButton.replace(self.ui.btnBack)
        self.ui.lblCurrentStreak.hide()
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
        self.ui.btnBack.clicked.connect(self.back_requested.emit)
        self.ui.scrollLeaderboard.setObjectName("leaderboardScrollArea")
        self.ui.scrollLeaderboard.setStyleSheet(LEADERBOARD_QSS)
        self.ui.leaderboardLayout.setSpacing(8)
        self.ui.leaderboardLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.ui.leaderboardLayout.setSizeConstraint(QLayout.SizeConstraint.SetMinAndMaxSize)
        self.ui.scrollLeaderboard.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._displayed_user_id = object()
        self._loading_user_id = None
        self._render_entries([])
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
            lambda: leaderboard_service.get_leaderboard(user_id=user_id), ready, failed,
            message="Loading the leaderboard…")

    def _render_entries(self, entries, *, failed=False):
        layout = self.ui.leaderboardLayout
        while layout.count():
            widget = layout.takeAt(0).widget()
            if widget is not None:
                widget.hide()
                widget.deleteLater()
        self.ui.lblCurrentStreak.setText("0 Days")
        if failed:
            layout.addWidget(QLabel("We couldn't load the leaderboard. Please try again.",
                                   self.ui.leaderboardContainer))
            retry = QPushButton("Retry", self.ui.leaderboardContainer)
            retry.setCursor(Qt.CursorShape.PointingHandCursor)
            retry.setStyleSheet("QPushButton { background: #f7f7dc; color: #526021; border: 1px solid #a9bd43; border-radius: 12px; padding: 8px 18px; }")
            retry.clicked.connect(self.refresh)
            layout.addWidget(retry)
            return
        for entry in entries:
            rank = entry["rank_position"]
            current = entry["is_current_user"]
            row = QFrame(self.ui.leaderboardContainer)
            row.setObjectName("leaderboardEntry")
            row.setProperty("class", f"leaderboardRank{rank}" if rank in (1, 2, 3)
                            else "leaderboardCurrentUser" if current else "leaderboardNormal")
            row.setProperty("user_id", entry["user_id"])
            row.setProperty("rank_position", rank)
            row.setProperty("currentUser", current)
            columns = QHBoxLayout(row)
            columns.setContentsMargins(20, 4, 20, 4)
            columns.setSpacing(12)
            medal = {1: "\U0001f947", 2: "\U0001f948", 3: "\U0001f949"}.get(rank)
            values = [
                ("rank", medal or str(rank), 0, Qt.AlignmentFlag.AlignCenter),
                ("username", "YOU" if current else entry["username"], 0, Qt.AlignmentFlag.AlignLeft),
                ("streak", f'Streak {entry["current_streak"]}', 160, Qt.AlignmentFlag.AlignCenter),
                ("badges", f'Badges: {entry["badges_unlocked"]}/20', 180, Qt.AlignmentFlag.AlignRight),
            ]
            for name, text, width, alignment in values:
                label = QLabel(text, row)
                label.setObjectName(name)
                label.setProperty("class", ("leaderboardMedal" if medal else "leaderboardRank")
                                  if name == "rank" else f"leaderboard{name.title()}")
                label.setProperty("currentUser", current)
                label.setTextFormat(Qt.TextFormat.PlainText)
                if name == 'username':
                    label.setWordWrap(True)
                    label.setToolTip(entry['username'])
                label.setAlignment(alignment | Qt.AlignmentFlag.AlignVCenter)
                if width:
                    label.setFixedWidth(width)
                columns.addWidget(label, 1 if name == "username" else 0)
            layout.addWidget(row)
            if entry["is_current_user"]:
                self.ui.lblCurrentStreak.setText(f'{entry["current_streak"]} Days')
        if not entries:
            layout.addWidget(QLabel("No leaderboard entries yet.", self.ui.leaderboardContainer))

    def showEvent(self, event):
        self.refresh()
        super().showEvent(event)

    def hideEvent(self, event):
        self.loading.cancel()
        super().hideEvent(event)

    def closeEvent(self, event):
        self.loading.cancel()
        super().closeEvent(event)
