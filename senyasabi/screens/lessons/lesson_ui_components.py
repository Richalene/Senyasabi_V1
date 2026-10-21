"""Reusable modern Lesson UI layout matching the updated Figma design."""
from pathlib import Path
from PySide6.QtCore import Qt, Signal, QRectF, QTimer
from PySide6.QtGui import QPainter, QPixmap, QColor, QPainterPath
from PySide6.QtWidgets import (QWidget, QLabel, QPushButton, QVBoxLayout,
                              QHBoxLayout, QSizePolicy)
from screens.camera_preview import RoundedCameraPreview
from screens.minigames.minigame_ui_components import CircularActionButton

ROOT = Path(__file__).resolve().parents[2]


class LessonHeader(QWidget):
    """
    Lesson header with SenyaSabi logo (top-left) and Back & Close buttons (top-right).
    """
    back_requested = Signal()
    close_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(90)
        self.setStyleSheet("background: transparent;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 10)

        # SenyaSabi Logo
        self.logo = QLabel(self)
        logo_path = ROOT / "resources/img/ui/senyasabi_logo_header.png"
        if logo_path.exists():
            self.logo.setPixmap(QPixmap(str(logo_path)))
        self.logo.setScaledContents(True)
        self.logo.setFixedSize(220, 45)
        layout.addWidget(self.logo, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        layout.addStretch()

        # Circular Back Button
        self.btn_back = QPushButton(self)
        self.btn_back.setFixedSize(48, 48)
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        back_icon_path = str(ROOT / "resources/img/ui/lesson_back_btn.png").replace("\\", "/")
        self.btn_back.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; border-image: url({back_icon_path}) 0 0 0 0 stretch stretch; }} "
            "QPushButton:hover { transform: scale(1.08); }"
        )
        self.btn_back.clicked.connect(self.back_requested.emit)
        layout.addWidget(self.btn_back)

        layout.addSpacing(16)

        # Close Button '✕'
        self.btn_close = QPushButton(self)
        self.btn_close.setFixedSize(48, 48)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        close_icon_path = str(ROOT / "resources/img/ui/close_btn.png").replace("\\", "/")
        self.btn_close.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; border-image: url({close_icon_path}) 0 0 0 0 stretch stretch; }} "
            "QPushButton:hover { transform: scale(1.1); }"
        )
        self.btn_close.clicked.connect(self.close_requested.emit)
        layout.addWidget(self.btn_close)


class LessonAvatarCard(QWidget):
    """
    Left amber card displaying the avatar performing the sign or playing a video.
    Supports pause overlay with large amber pause bars.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(700, 700)
        self.pixmap_sign = QPixmap()
        self.is_paused = False

    def set_sign_pixmap(self, pixmap):
        self.pixmap_sign = pixmap if pixmap and not pixmap.isNull() else QPixmap()
        self.update()

    def set_paused(self, paused):
        self.is_paused = paused
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)

        card_rect = QRectF(0, 0, self.width(), self.height())
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#F9BD49"))
        painter.drawRoundedRect(card_rect, 40, 40)

        if not self.pixmap_sign.isNull():
            target_rect = card_rect.adjusted(20, 20, -20, -20)
            scaled = self.pixmap_sign.scaled(
                int(target_rect.width()), int(target_rect.height()),
                Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            x = target_rect.x() + (target_rect.width() - scaled.width()) / 2
            y = target_rect.y() + (target_rect.height() - scaled.height()) / 2
            painter.drawPixmap(int(x), int(y), scaled)

        if self.is_paused:
            painter.setBrush(QColor(0, 0, 0, 70))
            painter.drawRoundedRect(card_rect, 40, 40)

            bar_w = 40
            bar_h = 160
            gap = 35
            cx, cy = self.width() / 2, self.height() / 2
            painter.setBrush(QColor("#FFAE00"))
            painter.drawRoundedRect(QRectF(cx - gap / 2 - bar_w, cy - bar_h / 2, bar_w, bar_h), 15, 15)
            painter.drawRoundedRect(QRectF(cx + gap / 2, cy - bar_h / 2, bar_w, bar_h), 15, 15)


class LessonFeedbackOverlay(QWidget):
    """
    Success overlay on top of the camera container:
    - 98% Accuracy pill badge at the top
    - Large green circle with white checkmark in center
    - 'You are a Natural!' encouragement text at the bottom
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.hide()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 40, 20, 40)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 1. Accuracy Pill Badge
        self.lbl_accuracy = QLabel("98% Accuracy", self)
        self.lbl_accuracy.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_accuracy.setFixedHeight(48)
        self.lbl_accuracy.setStyleSheet(
            "QLabel {"
            "  background-color: #FAFFDC;"
            "  color: #78A826;"
            "  font-family: 'Segoe UI', sans-serif;"
            "  font-size: 26px;"
            "  font-weight: bold;"
            "  font-style: italic;"
            "  border-radius: 24px;"
            "  padding: 0 25px;"
            "}"
        )
        layout.addWidget(self.lbl_accuracy, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()

        # 2. Big Success Check Badge (260x260)
        self.lbl_badge = QLabel(self)
        self.lbl_badge.setFixedSize(260, 260)
        badge_path = ROOT / "resources/img/ui/success_check_badge.png"
        if badge_path.exists():
            self.lbl_badge.setPixmap(QPixmap(str(badge_path)))
        self.lbl_badge.setScaledContents(True)
        layout.addWidget(self.lbl_badge, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()

        # 3. Encouragement Text
        self.lbl_message = QLabel("You are a Natural!", self)
        self.lbl_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_message.setStyleSheet(
            "QLabel {"
            "  color: #FFFFFF;"
            "  font-family: 'Segoe UI', sans-serif;"
            "  font-size: 32px;"
            "  font-weight: bold;"
            "  font-style: italic;"
            "  background: transparent;"
            "}"
        )
        layout.addWidget(self.lbl_message, alignment=Qt.AlignmentFlag.AlignCenter)

    def show_success(self, accuracy_pct=98, message="You are a Natural!"):
        self.lbl_accuracy.setText(f"{accuracy_pct}% Accuracy")
        self.lbl_accuracy.setStyleSheet(
            "background-color: #FAFFDC; color: #78A826; "
            "font-family: 'Segoe UI', sans-serif; font-size: 26px; "
            "font-weight: bold; font-style: italic; border-radius: 24px; padding: 0 25px;"
        )
        self.lbl_message.setText(message)
        badge_path = ROOT / "resources/img/ui/success_check_badge.png"
        if badge_path.exists():
            self.lbl_badge.setPixmap(QPixmap(str(badge_path)))
        self.show()
        self.raise_()

    def show_retry(self, accuracy_pct=28, message="Let's Try Again"):
        self.lbl_accuracy.setText(f"{accuracy_pct}% Accuracy")
        self.lbl_accuracy.setStyleSheet(
            "background-color: #FAFFDC; color: #E53935; "
            "font-family: 'Segoe UI', sans-serif; font-size: 26px; "
            "font-weight: bold; font-style: italic; border-radius: 24px; padding: 0 25px;"
        )
        self.lbl_message.setText(message)
        # Red cross icon matching Wireframe Page 57
        pix = QPixmap(260, 260)
        pix.fill(Qt.GlobalColor.transparent)
        from PySide6.QtGui import QPainter, QBrush, QColor, QPen
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor("#E53935")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(10, 10, 240, 240)
        pen = QPen(QColor("#FFFFFF"), 28, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(80, 80, 180, 180)
        painter.drawLine(180, 80, 80, 180)
        painter.end()
        self.lbl_badge.setPixmap(pix)
        self.show()
        self.raise_()


class ModernLessonLayout(QWidget):
    """
    Standard layout component shared across Alphabet, Spelling, and Word lessons:
    - Foliage background
    - Top header with logo, back, close
    - Cream container card with rounded corners
    - Left avatar card
    - Center vertical control bar (Next, Play/Pause, Replay, Camera Toggle)
    - Right camera view with fill_crop=True and success feedback overlay
    """
    next_clicked = Signal()
    play_pause_clicked = Signal()
    replay_clicked = Signal()
    cam_toggle_clicked = Signal()
    back_requested = Signal()
    close_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(1920, 1080)

        # Background
        self.bg_label = QLabel(self)
        self.bg_label.setGeometry(0, 0, 1920, 1080)
        self.bg_label.setStyleSheet("background-color: #C2D076;")

        # Header
        self.header = LessonHeader(self)
        self.header.setGeometry(0, 0, 1920, 90)
        self.header.back_requested.connect(self.back_requested.emit)
        self.header.close_requested.connect(self.close_requested.emit)

        # Main Cream Card Container
        self.card = QWidget(self)
        self.card.setGeometry(50, 95, 1820, 935)
        self.card.setStyleSheet("QWidget { background-color: #FAFFDC; border-radius: 40px; }")

        # Left Avatar Card
        self.avatar_card = LessonAvatarCard(self.card)
        self.avatar_card.move(90, 115)

        # Center Action Buttons Column
        self.controls_col = QWidget(self.card)
        self.controls_col.setGeometry(830, 160, 100, 610)
        self.controls_col.setStyleSheet("background: transparent;")
        c_layout = QVBoxLayout(self.controls_col)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(35)
        c_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 1. Next button
        self.btn_next = CircularActionButton("next", self.controls_col)
        self.btn_next.clicked.connect(self.next_clicked.emit)
        c_layout.addWidget(self.btn_next)

        # 2. Play / Pause button
        self.btn_pause = CircularActionButton("pause", self.controls_col)
        self.btn_pause.clicked.connect(self.play_pause_clicked.emit)
        c_layout.addWidget(self.btn_pause)

        # 3. Replay button
        self.btn_replay = CircularActionButton("replay", self.controls_col)
        self.btn_replay.clicked.connect(self.replay_clicked.emit)
        c_layout.addWidget(self.btn_replay)

        # 4. Camera toggle button
        self.btn_cam = QPushButton(self.controls_col)
        self.btn_cam.setFixedSize(70, 70)
        self.btn_cam.setCursor(Qt.CursorShape.PointingHandCursor)
        self.set_camera_active(True)
        self.btn_cam.clicked.connect(self.cam_toggle_clicked.emit)
        c_layout.addWidget(self.btn_cam)

        # Right: Camera Container Card
        self.camera_container = QWidget(self.card)
        self.camera_container.setGeometry(970, 115, 760, 700)
        self.camera_container.setStyleSheet("QWidget { background-color: #405768; border-radius: 40px; }")

        cam_layout = QVBoxLayout(self.camera_container)
        cam_layout.setContentsMargins(15, 15, 15, 15)

        # Camera feed (fill_crop=True for edge-to-edge video inside rounded corners)
        self.camera = RoundedCameraPreview("Opening camera...", self.camera_container, radius=35, fill_crop=True)
        self.camera.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cam_layout.addWidget(self.camera)

        # Success Overlay
        self.feedback_overlay = LessonFeedbackOverlay(self.camera_container)
        self.feedback_overlay.setGeometry(0, 0, 760, 700)

    def set_camera_active(self, active: bool):
        icon_name = "btn_cam_off.png" if active else "btn_cam_on.png"
        path = str(ROOT / "resources/img/ui" / icon_name).replace("\\", "/")
        self.btn_cam.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; border-image: url({path}) 0 0 0 0 stretch stretch; }} "
            "QPushButton:hover { transform: scale(1.08); }"
        )

