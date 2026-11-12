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

        # Transparent / styled buttons over 'Let's Go!' and 'Go Back'
        self.btn_start = QPushButton(self)
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.clicked.connect(self.start_requested.emit)

        self.btn_back = QPushButton(self)
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.clicked.connect(self.back_requested.emit)
        self.back_button = self.btn_back

        self._scale_layout()

    def _apply_button_styles(self, s):
        r = max(4, int(40 * s))
        self.btn_start.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; border-radius: {r}px; }} "
            "QPushButton:hover { background: rgba(255, 255, 255, 0.25); }"
        )
        self.btn_back.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; border-radius: {r}px; }} "
            "QPushButton:hover { background: rgba(0, 0, 0, 0.08); }"
        )

    def _scale_layout(self):
        w, h = self.width(), self.height()
        if w < 2 or h < 2:
            return
        s = max(0.05, min(w / self.BASE_W, h / self.BASE_H))
        ox = (w - self.BASE_W * s) / 2
        oy = (h - self.BASE_H * s) / 2

        def place(widget, x, y, bw, bh):
            widget.setGeometry(int(ox + x * s), int(oy + y * s),
                               max(1, int(bw * s)), max(1, int(bh * s)))

        place(self.bg_label, 0, 0, self.BASE_W, self.BASE_H)
        place(self.btn_start, 390, 810, 300, 110)
        place(self.btn_back, 730, 810, 300, 110)

        if self._last_scale != s:
            self._last_scale = s
            self._apply_button_styles(s)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._scale_layout()


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
    help_requested = Signal()

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

        # Help button '?'
        self.btn_help = QPushButton(self)
        self.btn_help.setFixedSize(48, 48)
        self.btn_help.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_help.setText("?")
        self.btn_help.setToolTip("Help & Rules")
        self.btn_help.setStyleSheet("""
            QPushButton {
                background-color: #FFFDF0;
                color: #4F3222;
                border: 2.5px solid #D6DFA0;
                border-radius: 24px;
                font-family: 'Cherry Bomb One', cursive, sans-serif;
                font-size: 24px;
                padding-bottom: 2px;
            }
            QPushButton:hover {
                background-color: #FAFFDC;
                border-color: #8C9F3E;
                color: #2F1E14;
            }
            QPushButton:pressed {
                background-color: #E8EFC0;
            }
        """)
        self.btn_help.clicked.connect(self.help_requested.emit)
        self._layout.addWidget(self.btn_help, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self._layout.addSpacing(12)

        # Close button
        self.btn_close = QPushButton(self)
        self.btn_close.setFixedSize(48, 48)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setToolTip("Exit activity")
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
        self.btn_help.setFixedSize(max(1, int(48 * s)), max(1, int(48 * s)))
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
        self.state = "filled" if letter else "empty"
        self.setFixedSize(self._base_size, self._base_size)
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
        s = self._scale
        bw = max(1, round(3 * s))
        bw_active = max(1, round(3.5 * s))
        radius = max(4, int(20 * s))
        font = (
            "  font-family: 'Segoe UI', Arial, sans-serif;"
            f"  font-size: {max(8, int(42 * s))}px;"
            "  font-weight: 800;"
        )
        if self.state == "empty":
            self.setStyleSheet(
                "QLabel {"
                "  background-color: #FFFDF0;"
                "  color: #3C2415;"
                f"  border: {bw}px solid #D5C9A9;"
                f"  border-radius: {radius}px;"
                "}"
            )
        elif self.state == "active":
            self.setStyleSheet(
                "QLabel {"
                "  background-color: #FFFFFF;"
                "  color: #FFAE00;"
                f"  border: {bw_active}px solid #FFAE00;"
                f"  border-radius: {radius}px;"
                f"{font}"
                "}"
            )
        elif self.state == "correct":
            self.setStyleSheet(
                "QLabel {"
                "  background-color: #BFD379;"
                "  color: #1E330C;"
                f"  border: {bw}px solid #94AB45;"
                f"  border-radius: {radius}px;"
                f"{font}"
                "}"
            )
        elif self.state == "wrong":
            self.setStyleSheet(
                "QLabel {"
                "  background-color: #FFB3A7;"
                "  color: #661D17;"
                f"  border: {bw}px solid #E06D5E;"
                f"  border-radius: {radius}px;"
                f"{font}"
                "}"
            )
        elif self.state == "revealed":
            self.setStyleSheet(
                "QLabel {"
                "  background-color: #FFE6A3;"
                "  color: #5C3B28;"
                f"  border: {bw}px dashed #E09800;"
                f"  border-radius: {radius}px;"
                f"{font}"
                "}"
            )
        else:  # filled
            self.setStyleSheet(
                "QLabel {"
                "  background-color: #FFAE00;"
                "  color: #2D1A0D;"
                f"  border: {bw}px solid #E69D00;"
                f"  border-radius: {radius}px;"
                f"{font}"
                "}"
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