"""Custom UI widgets and components for SenyaSabi minigames."""
from pathlib import Path
from PySide6.QtCore import Qt, Signal, QRectF, QSize
from PySide6.QtGui import QPainter, QPixmap, QColor, QFont, QPen, QPainterPath
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout

ROOT = Path(__file__).resolve().parents[2]


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


class MinigameScoreWidget(QWidget):
    """
    End-of-game Score Screen matching Figma reference:
    - Background: scores_bg.png
    - Title: 'Excellent!'
    - Score label: 'Score: 10/10' (or dynamic X/Y)
    - Green circular Next arrow button
    - Top-right close button '✕'
    """
    continue_requested = Signal()
    close_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(1920, 1080)
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

        # Dynamic Score Display: e.g. "5/5"
        self.lbl_score_val = QLabel(self)
        self.lbl_score_val.setGeometry(560, 680, 500, 220)
        self.lbl_score_val.setStyleSheet(
            "QLabel { font-family: 'Cherry Bomb One', 'Segoe UI', sans-serif; font-size: 130px; font-weight: bold; color: #704833; background: transparent; }"
        )
        self.lbl_score_val.setText("5/5")
        self.lbl_score_val.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Green arrow button
        self.btn_next = QPushButton(self)
        self.btn_next.setGeometry(220, 740, 170, 170)
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        arrow_icon_path = str(ROOT / "resources/img/ui/green_arrow_btn.png").replace("\\", "/")
        self.btn_next.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; border-image: url({arrow_icon_path}) 0 0 0 0 stretch stretch; }} "
            "QPushButton:hover { transform: scale(1.08); }"
        )
        self.btn_next.clicked.connect(self.continue_requested.emit)

    def set_score(self, score, total):
        self.lbl_score_val.setText(f"{score}/{total}")


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
        self.logo.setFixedSize(220, 45)
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
    Rounded golden-yellow tile box for letters.
    """
    def __init__(self, letter="", parent=None):
        super().__init__(parent)
        self.letter = letter.upper()
        self.setFixedSize(92, 92)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText(self.letter)
        self.update_style()

    def set_letter(self, letter):
        self.letter = letter.upper()
        self.setText(self.letter)
        self.update_style()

    def update_style(self):
        self.setStyleSheet(
            "QLabel {"
            "  background-color: #FFAE00;"
            "  color: #000000;"
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

