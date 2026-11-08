"""Custom UI widgets and components for SenyaSabi minigames."""
from pathlib import Path
from PySide6.QtCore import Qt, Signal, QRectF, QPointF, QSize
from PySide6.QtGui import QPainter, QPixmap, QColor, QFont, QPen, QPainterPath
from PySide6.QtWidgets import (QWidget, QLabel, QPushButton, QHBoxLayout,
                                QVBoxLayout, QSizePolicy)

try:
    from backend.paths import get_base_dir
    ROOT = get_base_dir()
except ImportError:
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

    Scales to whatever size it is given: the background keeps its 16:9
    aspect ratio (centered) and the clickable buttons follow it.
    """
    start_requested = Signal()
    back_requested = Signal()
    BASE_W, BASE_H = 1920, 1080

    def __init__(self, bg_image_name, parent=None):
        super().__init__(parent)
        self.setObjectName("howToPlayWidget")
        self.setMinimumSize(0, 0)
        self._last_scale = None

        self.bg_label = QLabel(self)
        pix = QPixmap(str(ROOT / "resources/img/games" / bg_image_name))
        self.bg_label.setPixmap(pix)
        self.bg_label.setScaledContents(True)
        # Never let the pixmap dictate a minimum size
        self.bg_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)

        # Fill any letterbox bars with the image's edge colour
        if not pix.isNull():
            edge = pix.toImage().pixelColor(0, 0).name()
            self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            self.setStyleSheet(f"#howToPlayWidget {{ background-color: {edge}; }}")

        # Buttons over 'Let's Go!' and 'Go Back'
        # Both buttons are styled as cohesive green pill buttons matching the SenyaSabi UI theme
        btn_style = (
            "QPushButton {"
            "  background-color: #C2D076;"
            "  color: #FFFFFF;"
            "  font-family: 'Segoe UI', Arial, sans-serif;"
            "  font-size: 32px;"
            "  font-weight: 700;"
            "  border: none;"
            "  border-radius: 44px;"
            "}"
            "QPushButton:hover {"
            "  background-color: #B1C065;"
            "}"
            "QPushButton:pressed {"
            "  background-color: #9FAF54;"
            "}"
        )

        self.btn_start = QPushButton("Let's Go!", self)
        self.btn_start.setGeometry(401, 840, 283, 88)
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.setStyleSheet(btn_style)
        self.btn_start.clicked.connect(self.start_requested.emit)

        self.btn_back = QPushButton("Go Back", self)
        self.btn_back.setGeometry(743, 840, 283, 88)
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.setStyleSheet(btn_style)
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
        self.setObjectName("minigameScoreWidget")
        self.setMinimumSize(0, 0)
        self._last_scale = None

        # Background scores_bg.png
        self.bg_label = QLabel(self)
        self.bg_label.setGeometry(0, 0, 1920, 1080)
        self.bg_label.setPixmap(QPixmap(str(ROOT / "resources/img/scores_bg.png")))
        self.bg_label.setScaledContents(True)
        self.bg_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)

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
        self.title_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_banner.setText("Excellent!")

        # Dynamic Score Display aligned directly next to baked 'Score:'
        self.lbl_score_val = QLabel(self)
        self.lbl_score_val.setGeometry(475, 640, 300, 140)
        self.lbl_score_val.setText("5/5")
        self.lbl_score_val.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Accuracy pill badge
        self.badge_acc = PillBadge("", self, background="#BFD379", foreground="#2D4014")
        self.badge_acc.setGeometry(800, 665, 280, 68)
        self.badge_acc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge_acc.setText("100% Accuracy")

        # Primary Continue Button
        self.btn_next = PillButton(
            "Continue  ➔", self, background="#8C9F3E", foreground="#FFFFFF",
            hover="#9DB446", pressed="#788934",
        )
        self.btn_next.setGeometry(170, 815, 340, 85)
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.clicked.connect(self.continue_requested.emit)

        # Secondary Play Again Button
        self.btn_replay = PillButton(
            "Play Again", self, background="#FFFDF0", foreground="#704833",
            hover="#FFF8E7", pressed="#F5ECCE", border="#D5C9A9", border_width=3.5,
        )
        self.btn_replay.setGeometry(540, 815, 270, 85)
        self.btn_replay.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_replay.clicked.connect(self.replay_requested.emit)

        self._apply_fonts(1.0)

    def _apply_fonts(self, scale):
        """Font sizes follow the window scale so text never overflows."""
        def px(v, lo):
            return max(lo, int(v * scale))
        self.title_banner.setStyleSheet(
            "QLabel {"
            "  background-color: #FFDE59;"
            "  color: #704833;"
            "  font-family: 'Cherry Bomb One', 'Segoe UI', sans-serif;"
            f"  font-size: {px(110, 14)}px;"
            "  font-weight: bold;"
            "}"
        )
        self.lbl_score_val.setStyleSheet(
            "QLabel {"
            "  font-family: 'Cherry Bomb One', 'Segoe UI', sans-serif;"
            f"  font-size: {px(85, 12)}px;"
            "  font-weight: bold;"
            "  color: #704833;"
            "  background: transparent;"
            "}"
        )
        self.badge_acc.setStyleSheet(
            "QLabel {"
            "  font-family: 'Segoe UI', sans-serif;"
            f"  font-size: {px(24, 8)}px;"
            "  font-weight: 700;"
            "}"
        )
        self.btn_next.setStyleSheet(
            "QPushButton {"
            "  font-family: 'Segoe UI', sans-serif;"
            f"  font-size: {px(30, 9)}px;"
            "  font-weight: 700;"
            "}"
        )
        self.btn_replay.setStyleSheet(
            "QPushButton {"
            "  font-family: 'Segoe UI', sans-serif;"
            f"  font-size: {px(26, 8)}px;"
            "  font-weight: 700;"
            "}"
        )

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

        if self._last_scale != scale:
            self._last_scale = scale
            self._apply_fonts(scale)

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
    Call set_scale(s) to resize it relative to its 1920x1080 design size.
    """
    close_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(90)
        self.setStyleSheet("background: transparent;")

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(40, 20, 40, 10)

        # SenyaSabi Logo
        self.logo = QLabel(self)
        self.logo.setPixmap(QPixmap(str(ROOT / "resources/img/ui/senyasabi_logo_header.png")))
        self.logo.setScaledContents(True)
        self.logo.setFixedSize(176, 60)
        self._layout.addWidget(self.logo, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self._layout.addStretch()

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
        self._layout.addWidget(self.btn_close, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    def set_scale(self, s):
        self.setFixedHeight(max(1, int(90 * s)))
        self._layout.setContentsMargins(int(40 * s), int(20 * s), int(40 * s), int(10 * s))
        self.logo.setFixedSize(max(1, int(176 * s)), max(1, int(60 * s)))
        self.btn_close.setFixedSize(max(1, int(48 * s)), max(1, int(48 * s)))


class LetterTile(QLabel):
    """
    Polished responsive letter tile with distinct visual states:
    - empty: subtle cream box awaiting typing
    - active: highlighted box showing the current typing slot
    - filled: bold golden-yellow tile with letter
    - correct: vibrant green celebration tile
    - wrong: soft error tint for incorrect attempt
    - revealed: golden dashed border when round expires
    Call set_scale(s) to resize tile, font, border and radius together.
    """
    def __init__(self, letter="", tile_size=100, parent=None):
        if isinstance(tile_size, QWidget):
            parent = tile_size
            tile_size = 100
        super().__init__(parent)
        self._base_size = int(tile_size)
        self._scale = 1.0
        self.letter = letter.upper()
        self.tile_size = int(tile_size)
        self.state = "filled" if letter else "empty"
        # BOOKMARK
        self.setFixedSize(self.tile_size, self.tile_size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText(self.letter)
        self.update_style()

    def set_scale(self, s):
        if abs(s - self._scale) < 1e-6:
            return
        self._scale = s
        side = max(1, int(self._base_size * s))
        self.setFixedSize(side, side)
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
        font_size = max(18, int(self.tile_size * 0.42))
        radius = max(8, int(self.tile_size * 0.20))
        border_w = max(2, int(self.tile_size * 0.03))

        if self.state == "empty":
            self.setStyleSheet(
                f"QLabel {{"
                f"  background-color: #FFFDF0;"
                f"  color: #3C2415;"
                f"  border: {border_w}px solid #D5C9A9;"
                f"  border-radius: {radius}px;"
                f"}}"
            )
        elif self.state == "active":
            self.setStyleSheet(
                f"QLabel {{"
                f"  background-color: #FFFFFF;"
                f"  color: #FFAE00;"
                f"  border: {border_w + 1}px solid #FFAE00;"
                f"  border-radius: {radius}px;"
                f"  font-family: 'Segoe UI', Arial, sans-serif;"
                f"  font-size: {font_size}px;"
                f"  font-weight: 800;"
                f"}}"
            )
        elif self.state == "correct":
            self.setStyleSheet(
                f"QLabel {{"
                f"  background-color: #BFD379;"
                f"  color: #1E330C;"
                f"  border: {border_w}px solid #94AB45;"
                f"  border-radius: {radius}px;"
                f"  font-family: 'Segoe UI', Arial, sans-serif;"
                f"  font-size: {font_size}px;"
                f"  font-weight: 800;"
                f"}}"
            )
        elif self.state == "wrong":
            self.setStyleSheet(
                f"QLabel {{"
                f"  background-color: #FFB3A7;"
                f"  color: #661D17;"
                f"  border: {border_w}px solid #E06D5E;"
                f"  border-radius: {radius}px;"
                f"  font-family: 'Segoe UI', Arial, sans-serif;"
                f"  font-size: {font_size}px;"
                f"  font-weight: 800;"
                f"}}"
            )
        elif self.state == "revealed":
            self.setStyleSheet(
                f"QLabel {{"
                f"  background-color: #FFE6A3;"
                f"  color: #5C3B28;"
                f"  border: {border_w}px dashed #E09800;"
                f"  border-radius: {radius}px;"
                f"  font-family: 'Segoe UI', Arial, sans-serif;"
                f"  font-size: {font_size}px;"
                f"  font-weight: 800;"
                f"}}"
            )
        else:  # filled
            self.setStyleSheet(
                f"QLabel {{"
                f"  background-color: #FFAE00;"
                f"  color: #2D1A0D;"
                f"  border: {border_w}px solid #E69D00;"
                f"  border-radius: {radius}px;"
                f"  font-family: 'Segoe UI', Arial, sans-serif;"
                f"  font-size: {font_size}px;"
                f"  font-weight: 800;"
                f"}}"
            )


class CircularActionButton(QPushButton):
    """
    Stylized circular control buttons:
    - Pause / Play (orange #FFAE00)
    - Replay (orange #FFAE00)
    - Next (grey #B4B4B4 or green #ACC412 when ready)
    Icons are drawn relative to the button size, so set_scale(s) resizes everything.
    """
    BASE_SIZE = 70

    def __init__(self, kind="pause", parent=None):
        super().__init__(parent)
        self.kind = kind
        self.setFixedSize(self.BASE_SIZE, self.BASE_SIZE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.is_green = False
        self.update_appearance()

    def set_scale(self, s):
        side = max(1, int(self.BASE_SIZE * s))
        if self.width() != side:
            self.setFixedSize(side, side)

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

        k = self.width() / float(self.BASE_SIZE)  # icon scale factor

        # Background circle
        if self.kind in ("pause", "play", "replay"):
            bg_color = QColor("#FFAE00")
        elif self.kind == "next":
            bg_color = QColor("#ACC412") if self.is_green else QColor("#B4B4B4")
        else:
            bg_color = QColor("#FFAE00")

        painter.setBrush(bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(2 * k, 2 * k, self.width() - 4 * k, self.height() - 4 * k))

        # Icon inside
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#FFFFFF") if self.kind == "next" and self.is_green else QColor("#5C3B28"))

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2

        if self.kind == "pause":
            # Two bars
            bar_w = 7 * k
            bar_h = 24 * k
            gap = 6 * k
            painter.setBrush(QColor("#704833"))
            painter.drawRoundedRect(QRectF(cx - gap / 2 - bar_w, cy - bar_h / 2, bar_w, bar_h), 3 * k, 3 * k)
            painter.drawRoundedRect(QRectF(cx + gap / 2, cy - bar_h / 2, bar_w, bar_h), 3 * k, 3 * k)

        elif self.kind == "play":
            # Right-pointing triangle
            painter.setBrush(QColor("#704833"))
            path = QPainterPath()
            path.moveTo(cx - 8 * k, cy - 14 * k)
            path.lineTo(cx + 14 * k, cy)
            path.lineTo(cx - 8 * k, cy + 14 * k)
            path.closeSubpath()
            painter.drawPath(path)

        elif self.kind == "replay":
            # Circular arrow
            painter.setPen(QPen(QColor("#704833"), 5 * k, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawArc(QRectF(cx - 15 * k, cy - 15 * k, 30 * k, 30 * k), 45 * 16, 270 * 16)
            # Arrow head
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#704833"))
            path = QPainterPath()
            path.moveTo(cx + 8 * k, cy - 18 * k)
            path.lineTo(cx + 18 * k, cy - 12 * k)
            path.lineTo(cx + 8 * k, cy - 6 * k)
            path.closeSubpath()
            painter.drawPath(path)

        elif self.kind == "next":
            # Right arrow
            painter.setPen(QPen(QColor("#FFFFFF"), 5 * k, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(QPointF(cx - 10 * k, cy), QPointF(cx + 10 * k, cy))
            painter.drawLine(QPointF(cx + 3 * k, cy - 7 * k), QPointF(cx + 10 * k, cy))
            painter.drawLine(QPointF(cx + 3 * k, cy + 7 * k), QPointF(cx + 10 * k, cy))

    def update_appearance(self):
        self.setStyleSheet("QPushButton { background: transparent; border: none; }")