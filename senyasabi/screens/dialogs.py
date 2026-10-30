"""
Shared dialogs matching wireframe specifications:
- WaitConfirmDialog (Pages 90 & 91)
- ComingSoonDialog (Page 26)
"""
from pathlib import Path
from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import QFontDatabase, QColor, QPainter, QPen, QBrush, QPainterPath
from PySide6.QtWidgets import (
    QApplication, QDialog, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
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
        self.reject()

    def showEvent(self, event):
        super().showEvent(event)
        parent = self.parentWidget()
        if parent:
            top = parent.window()
            if top:
                self.move(top.geometry().center() - self.rect().center())


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



class SpeakerButton(QPushButton):
    """Vector-rendered speaker icon matching SenyaSabi palette (no OS emoji)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(38, 38)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.muted = False

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)

        if self.underMouse():
            p.setBrush(QColor(191, 211, 121, 60))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(QRectF(2, 2, 34, 34), 8, 8)

        color = QColor("#4F3222")
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(color)

        # Speaker body: rect + cone
        p.drawRoundedRect(QRectF(7, 14, 5, 10), 1.5, 1.5)
        cone = QPainterPath()
        cone.moveTo(11, 14)
        cone.lineTo(18, 9)
        cone.lineTo(18, 29)
        cone.lineTo(11, 24)
        cone.closeSubpath()
        p.drawPath(cone)

        if not self.muted:
            p.setBrush(Qt.BrushStyle.NoBrush)
            pen = QPen(color, 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.drawArc(QRectF(13, 13, 12, 12), -45 * 16, 90 * 16)
            p.drawArc(QRectF(11, 9, 20, 20), -50 * 16, 100 * 16)
        else:
            pen = QPen(QColor("#C0392B"), 2.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.drawLine(8, 8, 30, 30)


class ExitButton(QPushButton):
    """Vector-rendered exit door icon with outgoing arrow (no broken unicode)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(36, 36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHints(QPainter.RenderHint.Antialiasing)

        p.setBrush(QColor("#FFF4E8"))
        p.setPen(QPen(QColor("#D5BCA9"), 1.5))
        p.drawRoundedRect(QRectF(1, 1, 34, 34), 8, 8)

        color = QColor("#8B251E") if self.underMouse() else QColor("#702A24")
        pen = QPen(color, 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

        door = QPainterPath()
        door.moveTo(17, 10)
        door.lineTo(10, 10)
        door.lineTo(10, 26)
        door.lineTo(17, 26)
        p.drawPath(door)

        p.drawLine(13, 18, 26, 18)
        p.drawLine(21, 13, 26, 18)
        p.drawLine(21, 23, 26, 18)


class CameraButton(QPushButton):
    """Vector-rendered camera icon button."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(36, 36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHints(QPainter.RenderHint.Antialiasing)

        p.setBrush(QColor("#F4F7E6"))
        p.setPen(QPen(QColor("#C4CE9B"), 1.5))
        p.drawRoundedRect(QRectF(1, 1, 34, 34), 8, 8)

        color = QColor("#3C4E1E") if self.underMouse() else QColor("#4F3222")
        pen = QPen(color, 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

        p.drawRoundedRect(QRectF(8, 13, 20, 14), 3, 3)
        p.drawEllipse(QRectF(14.5, 16.5, 7, 7))
        p.drawLine(12, 13, 14, 10)
        p.drawLine(14, 10, 18, 10)
        p.drawLine(18, 10, 20, 13)


class VolumeBarWidget(QWidget):
    """5-level volume bar indicator with smooth rounded bars and dragging."""
    volume_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(145, 42)
        self._level = 5  # 0 to 5
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_level(self, level: int):
        self._level = max(0, min(5, level))
        self.update()

    def mousePressEvent(self, event):
        self._handle_pos(event.position().x())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._handle_pos(event.position().x())

    def _handle_pos(self, x):
        bar_w = self.width() / 5
        level = int(x // bar_w) + 1
        self.set_level(level)
        self.volume_changed.emit(self._level * 20)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHints(QPainter.RenderHint.Antialiasing)

        bar_count = 5
        spacing = 7
        total_spacing = spacing * (bar_count - 1)
        bar_w = (self.width() - total_spacing) / bar_count
        base_h = 12
        h_step = 6

        for i in range(bar_count):
            h = base_h + i * h_step
            y = self.height() - h - 2
            x = i * (bar_w + spacing)

            if i < self._level:
                p.setBrush(QColor("#BFD379"))
                p.setPen(QPen(QColor("#94AB45"), 1.2))
            else:
                p.setBrush(QColor("#EBE8DA"))
                p.setPen(QPen(QColor("#D6D1BF"), 1.2))

            p.drawRoundedRect(QRectF(x, y, bar_w, h), 5, 5)


class MenuRowButton(QPushButton):
    """Interactive full-row button with label, icon, and hover styling."""
    def __init__(self, text, icon_widget, parent=None, is_danger=False):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(44)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)

        self.lbl = QLabel(text, self)
        color = "#7A2820" if is_danger else "#4F3222"
        weight = 700 if is_danger else 600
        self.lbl.setStyleSheet(
            f"font-family: 'Segoe UI', sans-serif; font-size: 16px; font-weight: {weight}; color: {color}; background: transparent;"
        )
        layout.addWidget(self.lbl)
        layout.addStretch()
        layout.addWidget(icon_widget)

        hover_bg = "rgba(224, 109, 94, 0.12)" if is_danger else "rgba(191, 211, 121, 0.22)"
        self.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; border-radius: 10px; }} "
            f"QPushButton:hover {{ background-color: {hover_bg}; }}"
        )


class MenuCalloutPopup(QWidget):
    """
    Speech-bubble style popup matching Wireframe Pages 12, 13, 22, 23, 46, 47:
    - Anchored right under the hamburger icon with top pointing beak
    - Top row: custom vector speaker mute/unmute button + 5 vertical volume bars
    - Middle row: Camera Setup option
    - Bottom row: 'Sign Out' label with vector exit door icon button
    """
    sign_out_requested = Signal()
    camera_requested = Signal()

    def __init__(self, anchor_widget, parent=None):
        super().__init__(parent or anchor_widget.window(), Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.anchor = anchor_widget
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(290, 250)

        from backend.audio_service import get_audio_service
        self.audio = get_audio_service()

        # Inner container for layout
        inner = QWidget(self)
        inner.setGeometry(25, 28, 240, 195)
        inner.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        # 1. Top Audio Row: Speaker icon button + Volume Bars
        audio_row = QHBoxLayout()
        audio_row.setSpacing(6)
        audio_row.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.btn_speaker = SpeakerButton(inner)
        self.btn_speaker.clicked.connect(self._toggle_mute)
        audio_row.addWidget(self.btn_speaker)

        self.volume_bars = VolumeBarWidget(inner)
        self.volume_bars.volume_changed.connect(self._on_volume_changed)
        audio_row.addWidget(self.volume_bars)
        layout.addLayout(audio_row)

        # Divider 1
        d1 = QWidget(inner)
        d1.setFixedHeight(1)
        d1.setStyleSheet("background-color: #E8E4D0; border: none;")
        layout.addWidget(d1)

        # 2. Camera Setup Row
        self.btn_camera = CameraButton(inner)
        self.row_camera = MenuRowButton("Camera Setup", self.btn_camera, inner)
        self.row_camera.clicked.connect(self._on_camera)
        self.btn_camera.clicked.connect(self._on_camera)
        layout.addWidget(self.row_camera)

        # Divider 2
        d2 = QWidget(inner)
        d2.setFixedHeight(1)
        d2.setStyleSheet("background-color: #E8E4D0; border: none;")
        layout.addWidget(d2)

        # 3. Bottom Sign Out Row
        self.btn_exit = ExitButton(inner)
        self.row_sign_out = MenuRowButton("Sign Out", self.btn_exit, inner, is_danger=True)
        self.row_sign_out.clicked.connect(self._on_sign_out)
        self.btn_exit.clicked.connect(self._on_sign_out)
        layout.addWidget(self.row_sign_out)

        self._sync_audio_state()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHints(QPainter.RenderHint.Antialiasing)

        ox, oy = 15, 18
        bw, bh = 260, 215
        beak_x = 205

        path = QPainterPath()
        path.moveTo(ox + 20, oy)
        path.lineTo(beak_x - 12, oy)
        path.lineTo(beak_x, oy - 12)
        path.lineTo(beak_x + 12, oy)
        path.lineTo(ox + bw - 20, oy)
        path.arcTo(ox + bw - 40, oy, 40, 40, 90, -90)
        path.lineTo(ox + bw, oy + bh - 20)
        path.arcTo(ox + bw - 40, oy + bh - 40, 40, 40, 0, -90)
        path.lineTo(ox + 20, oy + bh)
        path.arcTo(ox, oy + bh - 40, 40, 40, 270, -90)
        path.lineTo(ox, oy + 20)
        path.arcTo(ox, oy, 40, 40, 180, -90)
        path.closeSubpath()

        # Drop shadow
        p.setPen(Qt.PenStyle.NoPen)
        for offset, alpha in [(6, 12), (5, 18), (4, 25), (3, 35), (2, 45)]:
            p.setBrush(QColor(60, 40, 20, alpha))
            p.drawPath(path.translated(0, offset))

        # Main bubble body
        p.setBrush(QColor("#FFFDF0"))
        p.setPen(QPen(QColor("#D6DFA0"), 2.5))
        p.drawPath(path)

    def _sync_audio_state(self):
        is_muted = self.audio.muted or self.audio.volume == 0
        self.btn_speaker.muted = is_muted
        self.btn_speaker.update()
        if is_muted:
            self.volume_bars.set_level(0)
        else:
            self.volume_bars.set_level(max(1, round(self.audio.volume / 20)))

    def _toggle_mute(self):
        self.audio.toggle_mute()
        self._sync_audio_state()

    def _on_volume_changed(self, vol: int):
        self.audio.set_volume(vol)
        self.audio.set_muted(False)
        self._sync_audio_state()

    def _on_camera(self):
        self.close()
        self.camera_requested.emit()
        win = self.anchor.window()
        if hasattr(win, "camera_settings_requested"):
            win.camera_settings_requested.emit()
        elif hasattr(win, "show_camera_settings"):
            win.show_camera_settings()

    def _on_sign_out(self):
        self.close()
        self.sign_out_requested.emit()
        win = self.anchor.window()
        if hasattr(win, "logout_requested"):
            win.logout_requested.emit()
        elif hasattr(win, "logout"):
            win.logout()
        else:
            from backend import auth_service
            if hasattr(auth_service, 'logout_user'):
                auth_service.logout_user()
            elif hasattr(auth_service, 'clear_session'):
                auth_service.clear_session()
            app = QApplication.instance()
            if app is not None:
                for top in app.topLevelWidgets():
                    if hasattr(top, "show_login"):
                        top.show_login()
                        break

    def toggle_popup(self):
        if self.isVisible():
            self.close()
        else:
            self._sync_audio_state()
            pos = self.anchor.mapToGlobal(self.anchor.rect().bottomLeft())
            self.move(pos.x() - self.width() + self.anchor.width() + 14, pos.y() + 6)
            self.show()
