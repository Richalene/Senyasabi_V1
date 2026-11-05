"""Custom UI widgets and components for SenyaSabi minigames."""
from pathlib import Path
from PySide6.QtCore import Qt, Signal, QRectF, QSize
from PySide6.QtGui import QPainter, QPixmap, QColor, QFont, QPen, QPainterPath
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout

ROOT = Path(__file__).resolve().parents[2]


class PillButton(QPushButton):
    def __init__(self, text, parent=None, *, background, foreground, hover, pressed,
                 border=None, border_width=0):
        super().__init__(text, parent)
        self._background = QColor(background)
        self._foreground = QColor(foreground)
        self._hover = QColor(hover)
        self._pressed = QColor(pressed)
        self._border = QColor(border) if border else None
        self._border_width = border_width
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        if self.isDown():
            background = self._pressed
        elif self.underMouse():
            background = self._hover
        else:
            background = self._background
        painter.setBrush(background)
        if self._border and self._border_width:
            painter.setPen(QPen(self._border, self._border_width))
        else:
            painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)
        painter.setPen(self._foreground)
        painter.setFont(self.font())
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text())


class PillBadge(QLabel):
    def __init__(self, text="", parent=None, *, background, foreground,
                 border=None, border_width=0):
        super().__init__(text, parent)
        self._background = QColor(background)
        self._foreground = QColor(foreground)
        self._border = QColor(border) if border else None
        self._border_width = border_width

    def set_colors(self, background, foreground, border=None, border_width=0):
        self._background = QColor(background)
        self._foreground = QColor(foreground)
        self._border = QColor(border) if border else None
        self._border_width = border_width
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        if self._border and self._border_width:
            painter.setPen(QPen(self._border, self._border_width))
        else:
            painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._background)
        painter.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)
        painter.setPen(self._foreground)
        painter.setFont(self.font())
        painter.drawText(self.rect(), self.alignment(), self.text())


class HowToPlayWidget(QWidget):
    """
    How-To Instructions overlay screen for minigames:
    - SIGNSPRINTHOW.png, FINGERSPELLQUESTHOW.png, SIGNDETECTIVEHOW.png
    - Let's Go! (starts minigame)
    - Go Back (returns to minigame menu)
    """
    start_requested = Signal()
    back_requested = Signal()

    def __init__(self, bg_image_name, parent=None):
        super().__init__(parent)
        self.resize(1920, 1080)
        self.setObjectName("howToPlayWidget")

        self.bg_label = QLabel(self)
        self.bg_label.setGeometry(0, 0, 1920, 1080)
        self.bg_label.setPixmap(QPixmap(str(ROOT / "resources/img/games" / bg_image_name)))
        self.bg_label.setScaledContents(True)

        # Transparent / styled buttons over 'Let's Go!' and 'Go Back'
        self.btn_start = QPushButton(self)
        self.btn_start.setGeometry(390, 810, 300, 110)
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.setStyleSheet(
            "QPushButton { background: transparent; border: none; border-radius: 40px; } "
            "QPushButton:hover { background: rgba(255, 255, 255, 0.25); }"
        )
        self.btn_start.clicked.connect(self.start_requested.emit)

        self.btn_back = QPushButton(self)
        self.btn_back.setGeometry(730, 810, 300, 110)
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.setStyleSheet(
            "QPushButton { background: transparent; border: none; border-radius: 40px; } "
            "QPushButton:hover { background: rgba(0, 0, 0, 0.08); }"
        )
        self.btn_back.clicked.connect(self.back_requested.emit)
        self.back_button = self.btn_back


class MinigameScoreWidget(QWidget):
    """
    Polished end-of-game Score Screen:
    - Seamless dynamic Title banner inside yellow blob ("Excellent!", "Great Job!", "Well Done!", "Keep Going!")
    - Perfectly aligned score next to baked 'Score:'
    - Accuracy badge pill
    - Primary Continue button
    - Secondary Play Again button
    - Top-right close button '✕'
    """
    continue_requested = Signal()
    close_requested = Signal()
    replay_requested = Signal()
    BASE_WIDTH = 1920
    BASE_HEIGHT = 1080

    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(self.BASE_WIDTH, self.BASE_HEIGHT)
        self.setObjectName("minigameScoreWidget")

        # Background scores_bg.png
        self.bg_label = QLabel(self)
        self.bg_label.setGeometry(0, 0, 1920, 1080)
        self.bg_label.setPixmap(QPixmap(str(ROOT / "resources/img/scores_bg.png")))
        self.bg_label.setScaledContents(True)

        # Top-right Close Button
        self.btn_close = QPushButton(self)
        self.btn_close.setGeometry(1810, 30, 60, 60)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        close_icon_path = str(ROOT / "resources/img/ui/close_btn.png").replace("\\", "/")
        self.btn_close.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; border-image: url({close_icon_path}) 0 0 0 0 stretch stretch; }} "
            "QPushButton:hover { transform: scale(1.1); }"
        )
        self.btn_close.clicked.connect(self.close_requested.emit)

        # Seamless Title Banner inside yellow blob
        self.title_banner = QLabel(self)
        self.title_banner.setGeometry(160, 310, 1020, 220)
        self.title_banner.setStyleSheet(
            "QLabel {"
            "  background-color: #FFDE59;"
            "  color: #704833;"
            "  font-family: 'Cherry Bomb One', 'Segoe UI', sans-serif;"
            "  font-size: 110px;"
            "  font-weight: bold;"
            "}"
        )
        self.title_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_banner.setText("Excellent!")

        # Dynamic Score Display aligned directly next to baked 'Score:'
        self.lbl_score_val = QLabel(self)
        self.lbl_score_val.setGeometry(475, 640, 300, 140)
        self.lbl_score_val.setStyleSheet(
            "QLabel {"
            "  font-family: 'Cherry Bomb One', 'Segoe UI', sans-serif;"
            "  font-size: 85px;"
            "  font-weight: bold;"
            "  color: #704833;"
            "  background: transparent;"
            "}"
        )
        self.lbl_score_val.setText("5/5")
        self.lbl_score_val.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Accuracy pill badge
        self.badge_acc = PillBadge("", self, background="#BFD379", foreground="#2D4014")
        self.badge_acc.setGeometry(800, 665, 280, 68)
        self.badge_acc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge_acc.setStyleSheet(
            "QLabel {"
            "  font-family: 'Segoe UI', sans-serif;"
            "  font-size: 24px;"
            "  font-weight: 700;"
            "}"
        )
        self.badge_acc.setText("100% Accuracy")

        # Primary Continue Button
        self.btn_next = PillButton(
            "Continue  ➔", self, background="#8C9F3E", foreground="#FFFFFF",
            hover="#9DB446", pressed="#788934",
        )
        self.btn_next.setGeometry(170, 815, 340, 85)
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.setStyleSheet(
            "QPushButton {"
            "  font-family: 'Segoe UI', sans-serif;"
            "  font-size: 30px;"
            "  font-weight: 700;"
            "}"
        )
        self.btn_next.clicked.connect(self.continue_requested.emit)

        # Secondary Play Again Button
        self.btn_replay = PillButton(
            "Play Again", self, background="#FFFDF0", foreground="#704833",
            hover="#FFF8E7", pressed="#F5ECCE", border="#D5C9A9", border_width=3.5,
        )
        self.btn_replay.setGeometry(540, 815, 270, 85)
        self.btn_replay.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_replay.setStyleSheet(
            "QPushButton {"
            "  font-family: 'Segoe UI', sans-serif;"
            "  font-size: 26px;"
            "  font-weight: 700;"
            "}"
        )
        self.btn_replay.clicked.connect(self.replay_requested.emit)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.width() <= 0 or self.height() <= 0:
            return
        sx = self.width() / float(self.BASE_WIDTH)
        sy = self.height() / float(self.BASE_HEIGHT)
        scale = min(sx, sy)

        self.bg_label.setGeometry(0, 0, self.width(), self.height())
        self.btn_close.setGeometry(int(1810 * sx), int(30 * sy), max(1, int(60 * scale)), max(1, int(60 * scale)))
        self.title_banner.setGeometry(int(160 * sx), int(310 * sy), max(1, int(1020 * sx)), max(1, int(220 * sy)))
        self.lbl_score_val.setGeometry(int(475 * sx), int(640 * sy), max(1, int(300 * sx)), max(1, int(140 * sy)))
        self.badge_acc.setGeometry(int(800 * sx), int(665 * sy), max(1, int(280 * sx)), max(1, int(68 * sy)))
        self.btn_next.setGeometry(int(170 * sx), int(815 * sy), max(1, int(340 * sx)), max(1, int(85 * sy)))
        self.btn_replay.setGeometry(int(540 * sx), int(815 * sy), max(1, int(270 * sx)), max(1, int(85 * sy)))

    def set_score(self, score, total):
        self.lbl_score_val.setText(f"{score}/{total}")
        pct = int((score / total) * 100) if total > 0 else 0
        self.badge_acc.setText(f"{pct}% Accuracy")
        if pct >= 100:
            self.title_banner.setText("Excellent!")
            self.badge_acc.set_colors("#BFD379", "#2D4014")
        elif pct >= 80:
            self.title_banner.setText("Great Job!")
            self.badge_acc.set_colors("#FFDE59", "#5C3B28")
        elif pct >= 50:
            self.title_banner.setText("Well Done!")
            self.badge_acc.set_colors("#FFDE59", "#5C3B28")
        else:
            self.title_banner.setText("Keep Going!")
            self.badge_acc.set_colors("#FFB3A7", "#661D17")


class MinigameHeader(QWidget):
    """
    Standard Minigame Header with SenyaSabi logo (top-left) and Close '✕' (top-right).
    """
    close_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(90)
        self.setStyleSheet("background: transparent;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 10)

        # SenyaSabi Logo
        self.logo = QLabel(self)
        self.logo.setPixmap(QPixmap(str(ROOT / "resources/img/ui/senyasabi_logo_header.png")))
        self.logo.setScaledContents(True)
        self.logo.setFixedSize(176, 60)
        layout.addWidget(self.logo, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        layout.addStretch()

        # Close button
        self.btn_close = QPushButton(self)
        self.btn_close.setFixedSize(48, 48)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        close_icon_path = str(ROOT / "resources/img/ui/close_btn.png").replace("\\", "/")
        self.btn_close.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; border-image: url({close_icon_path}) 0 0 0 0 stretch stretch; }} "
            "QPushButton:hover { transform: scale(1.1); }"
        )
        self.btn_close.clicked.connect(self.close_requested.emit)
        layout.addWidget(self.btn_close, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)


class LetterTile(QLabel):
    """
    Polished responsive letter tile with distinct visual states:
    - empty: subtle cream box awaiting typing
    - active: highlighted box showing the current typing slot
    - filled: bold golden-yellow tile with letter
    - correct: vibrant green celebration tile
    - wrong: soft error tint for incorrect attempt
    - revealed: golden dashed border when round expires
    """
    def __init__(self, letter="", tile_size=100, parent=None):
        super().__init__(parent)
        self.letter = letter.upper()
        self.state = "filled" if letter else "empty"
        self.setFixedSize(tile_size, tile_size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText(self.letter)
        self.update_style()

    def set_letter(self, letter, state=None):
        self.letter = letter.upper()
        self.setText(self.letter)
        if state is not None:
            self.state = state
        else:
            self.state = "filled" if self.letter else "empty"
        self.update_style()

    def set_state(self, state):
        self.state = state
        self.update_style()

    def update_style(self):
        if self.state == "empty":
            self.setStyleSheet(
                "QLabel {"
                "  background-color: #FFFDF0;"
                "  color: #3C2415;"
                "  border: 3px solid #D5C9A9;"
                "  border-radius: 20px;"
                "}"
            )
        elif self.state == "active":
            self.setStyleSheet(
                "QLabel {"
                "  background-color: #FFFFFF;"
                "  color: #FFAE00;"
                "  border: 3.5px solid #FFAE00;"
                "  border-radius: 20px;"
                "  font-family: 'Segoe UI', Arial, sans-serif;"
                "  font-size: 42px;"
                "  font-weight: 800;"
                "}"
            )
        elif self.state == "correct":
            self.setStyleSheet(
                "QLabel {"
                "  background-color: #BFD379;"
                "  color: #1E330C;"
                "  border: 3px solid #94AB45;"
                "  border-radius: 20px;"
                "  font-family: 'Segoe UI', Arial, sans-serif;"
                "  font-size: 42px;"
                "  font-weight: 800;"
                "}"
            )
        elif self.state == "wrong":
            self.setStyleSheet(
                "QLabel {"
                "  background-color: #FFB3A7;"
                "  color: #661D17;"
                "  border: 3px solid #E06D5E;"
                "  border-radius: 20px;"
                "  font-family: 'Segoe UI', Arial, sans-serif;"
                "  font-size: 42px;"
                "  font-weight: 800;"
                "}"
            )
        elif self.state == "revealed":
            self.setStyleSheet(
                "QLabel {"
                "  background-color: #FFE6A3;"
                "  color: #5C3B28;"
                "  border: 3px dashed #E09800;"
                "  border-radius: 20px;"
                "  font-family: 'Segoe UI', Arial, sans-serif;"
                "  font-size: 42px;"
                "  font-weight: 800;"
                "}"
            )
        else:  # filled
            self.setStyleSheet(
                "QLabel {"
                "  background-color: #FFAE00;"
                "  color: #2D1A0D;"
                "  border: 3px solid #E69D00;"
                "  border-radius: 20px;"
                "  font-family: 'Segoe UI', Arial, sans-serif;"
                "  font-size: 42px;"
                "  font-weight: 800;"
                "}"
            )


class CircularActionButton(QPushButton):
    """
    Stylized circular control buttons:
    - Pause / Play (orange #FFAE00)
    - Replay (orange #FFAE00)
    - Next (grey #B4B4B4 or green #ACC412 when ready)
    """
    def __init__(self, kind="pause", parent=None):
        super().__init__(parent)
        self.kind = kind
        self.setFixedSize(70, 70)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.is_green = False
        self.update_appearance()

    def set_kind(self, kind, green=False):
        self.kind = kind
        self.is_green = green
        self.update()

    def set_green(self, green=True):
        self.is_green = green
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)

        # Background circle
        if self.kind in ("pause", "play", "replay"):
            bg_color = QColor("#FFAE00")
        elif self.kind == "next":
            bg_color = QColor("#ACC412") if self.is_green else QColor("#B4B4B4")
        else:
            bg_color = QColor("#FFAE00")

        painter.setBrush(bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(2, 2, self.width() - 4, self.height() - 4))

        # Icon inside
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#FFFFFF") if self.kind == "next" and self.is_green else QColor("#5C3B28"))

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2

        if self.kind == "pause":
            # Two bars
            bar_w = 7
            bar_h = 24
            gap = 6
            painter.setBrush(QColor("#704833"))
            painter.drawRoundedRect(QRectF(cx - gap / 2 - bar_w, cy - bar_h / 2, bar_w, bar_h), 3, 3)
            painter.drawRoundedRect(QRectF(cx + gap / 2, cy - bar_h / 2, bar_w, bar_h), 3, 3)

        elif self.kind == "play":
            # Right-pointing triangle
            painter.setBrush(QColor("#704833"))
            path = QPainterPath()
            path.moveTo(cx - 8, cy - 14)
            path.lineTo(cx + 14, cy)
            path.lineTo(cx - 8, cy + 14)
            path.closeSubpath()
            painter.drawPath(path)

        elif self.kind == "replay":
            # Circular arrow
            painter.setPen(QPen(QColor("#704833"), 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawArc(QRectF(cx - 15, cy - 15, 30, 30), 45 * 16, 270 * 16)
            # Arrow head
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#704833"))
            path = QPainterPath()
            path.moveTo(cx + 8, cy - 18)
            path.lineTo(cx + 18, cy - 12)
            path.lineTo(cx + 8, cy - 6)
            path.closeSubpath()
            painter.drawPath(path)

        elif self.kind == "next":
            # Right arrow
            painter.setPen(QPen(QColor("#FFFFFF"), 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(cx - 10, cy, cx + 10, cy)
            painter.drawLine(cx + 3, cy - 7, cx + 10, cy)
            painter.drawLine(cx + 3, cy + 7, cx + 10, cy)

    def update_appearance(self):
        self.setStyleSheet("QPushButton { background: transparent; border: none; }")

