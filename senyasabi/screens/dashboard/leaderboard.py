"""Controller for the existing leaderboard.ui form."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLayout, QWidget

from backend import leaderboard_service
from ui.leaderboard_ui import Ui_Leaderboard


class LeaderboardWindow(QWidget):
    back_requested = Signal()
    menu_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Leaderboard()
        self.ui.setupUi(self)
        self.ui.btnBack.clicked.connect(self.back_requested.emit)
        self.ui.btnMenu.clicked.connect(self.menu_requested.emit)
        self.ui.leaderboardLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.ui.leaderboardLayout.setSizeConstraint(QLayout.SizeConstraint.SetMinAndMaxSize)
        self.ui.scrollLeaderboard.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def refresh(self):
        layout = self.ui.leaderboardLayout
        while layout.count():
            widget = layout.takeAt(0).widget()
            if widget is not None:
                widget.hide()
                widget.deleteLater()
        self.ui.lblCurrentStreak.setText("0 Days")
        entries = leaderboard_service.get_leaderboard()
        for entry in entries:
            row = QFrame(self.ui.leaderboardContainer)
            row.setObjectName("currentUserRow" if entry["is_current_user"] else "leaderboardRow")
            row.setProperty("user_id", entry["user_id"])
            row.setMinimumHeight(54)
            columns = QHBoxLayout(row)
            columns.setContentsMargins(14, 8, 14, 8)
            rank = entry["rank_position"]
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, "")
            values = [("rank", f"{medal} #{rank}", 80),
                      ("username", entry["username"], 0),
                      ("streak", str(entry["current_streak"]), 130),
                      ("badges", str(entry["badges_unlocked"]), 130)]
            for name, text, width in values:
                label = QLabel(text, row)
                label.setObjectName(name)
                label.setTextFormat(Qt.TextFormat.PlainText)
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
