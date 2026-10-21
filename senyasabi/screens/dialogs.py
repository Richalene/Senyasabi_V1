"""
Shared dialogs matching wireframe specifications:
- WaitConfirmDialog (Pages 90 & 91)
- ComingSoonDialog (Page 26)
"""
from pathlib import Path
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QFontDatabase, QColor
from PySide6.QtWidgets import (
    QDialog, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGraphicsDropShadowEffect
)

ROOT = Path(__file__).resolve().parents[2]


def _ensure_font():
    font_path = ROOT / "resources/font/CherryBombOne-Regular.ttf"
    if font_path.exists():
        QFontDatabase.addApplicationFont(str(font_path))


class WaitConfirmDialog(QDialog):
    """
    Exit confirmation dialog matching Wireframe Pages 90 & 91:
    - Amber/yellow pill container with 'Wait!' in Cherry Bomb One
    - 'Are you sure you want to leave the game / lesson?'
    - 'Yes' (green) and 'No' (amber) pill buttons
    """
    confirmed = Signal()
    cancelled = Signal()

    def __init__(self, mode: str = "game", parent: QWidget | None = None):
        super().__init__(parent)
        _ensure_font()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(760, 420)

        # Main backdrop container
        container = QWidget(self)
        container.setGeometry(0, 0, 760, 420)
        container.setStyleSheet(
            "background-color: #FFFDF0; "
            "border: 4px solid #D6DFA0; "
            "border-radius: 40px;"
        )

        shadow = QGraphicsDropShadowEffect(container)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 8)
        container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(40, 36, 40, 36)
        layout.setSpacing(18)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 'Wait!' Title Pill Banner
        title_banner = QWidget(container)
        title_banner.setFixedHeight(105)
        title_banner.setStyleSheet(
            "background-color: #FFDE59; "
            "border-radius: 35px; "
            "border: none;"
        )
        banner_layout = QHBoxLayout(title_banner)
        banner_layout.setContentsMargins(0, 0, 0, 0)
        banner_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_wait = QLabel("Wait!", title_banner)
        lbl_wait.setStyleSheet(
            "font-family: 'Cherry Bomb One', cursive, sans-serif; "
            "font-size: 58px; "
            "color: #4F3222; "
            "background: transparent;"
        )
        banner_layout.addWidget(lbl_wait)
        layout.addWidget(title_banner)

        # Message Text
        target = "game" if mode == "game" else "lesson"
        lbl_msg = QLabel(f"Are you sure you want to leave the {target}?", container)
        lbl_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_msg.setStyleSheet(
            "font-family: 'Cherry Bomb One', cursive, sans-serif; "
            "font-size: 26px; "
            "color: #4F3222; "
            "background: transparent;"
        )
        layout.addWidget(lbl_msg)
        layout.addSpacing(6)

        # Buttons Row: Yes / No
        btn_row = QHBoxLayout()
        btn_row.setSpacing(28)
        btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_yes = QPushButton("Yes", container)
        self.btn_yes.setFixedSize(190, 65)
        self.btn_yes.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_yes.setStyleSheet(
            "QPushButton { "
            "  font-family: 'Cherry Bomb One', cursive, sans-serif; "
            "  font-size: 32px; "
            "  color: #4F3222; "
            "  background-color: #BFD379; "
            "  border-radius: 30px; "
            "  border: none; "
            "} "
            "QPushButton:hover { "
            "  background-color: #ADC362; "
            "}"
        )
        self.btn_yes.clicked.connect(self._on_yes)
        btn_row.addWidget(self.btn_yes)

        self.btn_no = QPushButton("No", container)
        self.btn_no.setFixedSize(190, 65)
        self.btn_no.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_no.setStyleSheet(
            "QPushButton { "
            "  font-family: 'Cherry Bomb One', cursive, sans-serif; "
            "  font-size: 32px; "
            "  color: #4F3222; "
            "  background-color: #FFDE59; "
            "  border-radius: 30px; "
            "  border: none; "
            "} "
            "QPushButton:hover { "
            "  background-color: #ECCB44; "
            "}"
        )
        self.btn_no.clicked.connect(self._on_no)
        btn_row.addWidget(self.btn_no)

        layout.addLayout(btn_row)

    def _on_yes(self):
        self.confirmed.emit()
        self.accept()

    def _on_no(self):
        self.cancelled.emit()
        self.reject()


class ComingSoonDialog(QDialog):
    """
    Coming Soon card matching Wireframe Page 26:
    - Pill label 'Coming Soon'
    - 'Building Bridges, One Sign at a Time.'
    - Descriptive message
    - 'Go Back' pill button
    """
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(760, 480)

        container = QWidget(self)
        container.setGeometry(0, 0, 760, 480)
        container.setStyleSheet(
            "background-color: #FFFDF0; "
            "border: 4px solid #D6DFA0; "
            "border-radius: 40px;"
        )

        shadow = QGraphicsDropShadowEffect(container)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 8)
        container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(44, 38, 44, 38)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 'Coming Soon' Pill Tag
        pill = QLabel("Coming Soon", container)
        pill.setFixedSize(160, 42)
        pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pill.setStyleSheet(
            "font-family: 'Segoe UI', sans-serif; "
            "font-size: 16px; "
            "font-weight: 600; "
            "color: #4F3222; "
            "background: transparent; "
            "border: 1.5px solid #4F3222; "
            "border-radius: 20px;"
        )
        layout.addWidget(pill)

        # Title
        title = QLabel("Building\nBridges, One\nSign at a Time.", container)
        title.setStyleSheet(
            "font-family: 'Segoe UI', sans-serif; "
            "font-size: 38px; "
            "font-weight: 800; "
            "line-height: 1.1; "
            "color: #1A1A1A; "
            "background: transparent;"
        )
        layout.addWidget(title)

        # Subtitle
        desc = QLabel(
            "We appreciate your patience as we continue to work on a\n"
            "few features and, eventually, more complex and advanced\n"
            "learning courses.", container
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(
            "font-family: 'Segoe UI', sans-serif; "
            "font-size: 16px; "
            "color: #555555; "
            "line-height: 1.4; "
            "background: transparent;"
        )
        layout.addWidget(desc)
        layout.addSpacing(10)

        # 'Go Back' Button
        btn_back = QPushButton("Go Back", container)
        btn_back.setFixedSize(180, 54)
        btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_back.setStyleSheet(
            "QPushButton { "
            "  font-family: 'Segoe UI', sans-serif; "
            "  font-size: 18px; "
            "  font-weight: 600; "
            "  color: #4F3222; "
            "  background-color: #BFD379; "
            "  border-radius: 26px; "
            "  border: none; "
            "} "
            "QPushButton:hover { "
            "  background-color: #ADC362; "
            "}"
        )
        btn_back.clicked.connect(self.accept)
        layout.addWidget(btn_back)



class VolumeBarWidget(QWidget):
    """5-level volume bar indicator matching wireframe Pages 12, 13, 22, 23, 46, 47."""
    volume_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(140, 48)
        self._level = 5  # 1 to 5
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_level(self, level: int):
        self._level = max(0, min(5, level))
        self.update()

    def mousePressEvent(self, event):
        x = event.position().x()
        bar_w = self.width() / 5
        level = int(x // bar_w) + 1
        self.set_level(level)
        self.volume_changed.emit(self._level * 20)

    def paintEvent(self, event):
        from PySide6.QtGui import QPainter, QBrush, QColor
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 5 vertical bars with increasing heights
        bar_count = 5
        spacing = 6
        total_spacing = spacing * (bar_count - 1)
        bar_w = (self.width() - total_spacing) / bar_count
        base_h = 14
        h_step = 6

        for i in range(bar_count):
            h = base_h + i * h_step
            y = self.height() - h
            x = i * (bar_w + spacing)
            
            if i < self._level:
                color = QColor("#BFD379")  # Active olive-green
            else:
                color = QColor("#DDDDBB")  # Inactive muted
            
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRectF(x, y, bar_w, h), 4, 4)


class MenuCalloutPopup(QWidget):
    """
    Speech-bubble style popup matching Wireframe Pages 12, 13, 22, 23, 46, 47:
    - Anchored right under the hamburger icon
    - Top row: speaker mute/unmute button + 5 vertical volume bars
    - Horizontal divider
    - Bottom row: 'Sign Out' label with exit door icon button
    """
    sign_out_requested = Signal()

    def __init__(self, anchor_widget, parent=None):
        super().__init__(parent or anchor_widget.window(), Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.anchor = anchor_widget
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(260, 160)

        from backend.audio_service import get_audio_service
        self.audio = get_audio_service()

        container = QWidget(self)
        container.setGeometry(10, 10, 240, 140)
        container.setStyleSheet(
            "background-color: #FFFDF0; "
            "border: 2px solid #D6DFA0; "
            "border-radius: 20px;"
        )

        shadow = QGraphicsDropShadowEffect(container)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 6)
        container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(10)

        # Top Audio Row: Speaker icon button + Volume Bars
        audio_row = QHBoxLayout()
        audio_row.setSpacing(12)
        audio_row.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.btn_speaker = QPushButton(container)
        self.btn_speaker.setFixedSize(36, 36)
        self.btn_speaker.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_speaker.setStyleSheet(
            "QPushButton { "
            "  background: transparent; "
            "  border: none; "
            "  font-size: 20px; "
            "  color: #4F3222; "
            "}"
        )
        self._update_speaker_icon()
        self.btn_speaker.clicked.connect(self._toggle_mute)
        audio_row.addWidget(self.btn_speaker)

        self.volume_bars = VolumeBarWidget(container)
        self.volume_bars.set_level(max(1, round(self.audio.volume / 20)))
        self.volume_bars.volume_changed.connect(self._on_volume_changed)
        audio_row.addWidget(self.volume_bars)

        layout.addLayout(audio_row)

        # Divider
        divider = QWidget(container)
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: #E2DECA; border: none;")
        layout.addWidget(divider)

        # Bottom Sign Out Row
        sign_out_row = QHBoxLayout()
        sign_out_row.setContentsMargins(4, 0, 4, 0)
        sign_out_row.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        lbl_sign_out = QLabel("Sign Out", container)
        lbl_sign_out.setStyleSheet(
            "font-family: 'Segoe UI', sans-serif; "
            "font-size: 18px; "
            "font-weight: 600; "
            "color: #4F3222; "
            "background: transparent;"
        )
        sign_out_row.addWidget(lbl_sign_out)
        sign_out_row.addStretch()

        btn_exit = QPushButton("⮞", container)
        btn_exit.setFixedSize(36, 36)
        btn_exit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_exit.setStyleSheet(
            "QPushButton { "
            "  background: transparent; "
            "  border: 2px solid #4F3222; "
            "  border-radius: 8px; "
            "  font-size: 16px; "
            "  font-weight: 700; "
            "  color: #4F3222; "
            "} "
            "QPushButton:hover { "
            "  background-color: rgba(79, 50, 34, 0.1); "
            "}"
        )
        btn_exit.clicked.connect(self._on_sign_out)
        sign_out_row.addWidget(btn_exit)

        layout.addLayout(sign_out_row)

    def _update_speaker_icon(self):
        if self.audio.muted or self.audio.volume == 0:
            self.btn_speaker.setText("🔇")
        else:
            self.btn_speaker.setText("🔊")

    def _toggle_mute(self):
        self.audio.toggle_mute()
        self._update_speaker_icon()
        if self.audio.muted:
            self.volume_bars.set_level(0)
        else:
            self.volume_bars.set_level(max(1, round(self.audio.volume / 20)))

    def _on_volume_changed(self, vol: int):
        self.audio.set_volume(vol)
        self.audio.set_muted(False)
        self._update_speaker_icon()

    def _on_sign_out(self):
        self.close()
        # Look for logout on parent window or app controller
        win = self.anchor.window()
        if hasattr(win, "logout_requested"):
            win.logout_requested.emit()
        elif hasattr(win, "logout"):
            win.logout()
        else:
            from backend import auth_service
            auth_service.clear_session()
            app = QApplication.instance()
            for top in app.topLevelWidgets():
                if hasattr(top, "show_login"):
                    top.show_login()
                    break

    def toggle_popup(self):
        if self.isVisible():
            self.close()
        else:
            pos = self.anchor.mapToGlobal(self.anchor.rect().bottomLeft())
            self.move(pos.x() - self.width() + self.anchor.width() + 10, pos.y() + 6)
            self.show()
