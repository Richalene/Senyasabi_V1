"""Reusable modern Lesson UI layout matching the updated Figma design."""
from pathlib import Path
from PySide6.QtCore import Qt, Signal, QRectF, QTimer
from PySide6.QtGui import QPainter, QPixmap, QColor, QPainterPath, QPen, QFont
from PySide6.QtWidgets import (QWidget, QLabel, QPushButton, QVBoxLayout,
                              QHBoxLayout, QSizePolicy)
from screens.camera_preview import RoundedCameraPreview
from screens.minigames.minigame_ui_components import CircularActionButton

ROOT = Path(__file__).resolve().parents[2]


class _CircularAccuracyGauge(QWidget):
    """Circular percentage ring indicator for LessonResultsWidget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(165, 165)
        self._percent = 0

    def set_percent(self, percent: int):
        try:
            import math
            val = float(percent)
            if not math.isfinite(val):
                val = 0.0
        except Exception:
            val = 0.0
        self._percent = max(0, min(100, int(round(val))))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)

        rect = QRectF(14, 14, self.width() - 28, self.height() - 28)

        # Soft inner fill
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#FFFDF0"))
        painter.drawEllipse(rect)

        # Background track ring
        track_pen = QPen(QColor("#E2D9C8"), 15, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(track_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(rect)

        # Progress arc starting at 12 o'clock (90 degrees), clockwise
        if self._percent > 0:
            arc_color = QColor("#8C9F3E") if self._percent >= 75 else QColor("#FFAE00")
            arc_pen = QPen(arc_color, 15, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(arc_pen)
            span_angle = int(-360 * 16 * (self._percent / 100.0))
            painter.drawArc(rect, 90 * 16, span_angle)

        # Center percentage text
        painter.setPen(QColor("#5C3B28"))
        font = QFont("Cherry Bomb One", 26, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{self._percent}%")
        painter.end()


class LessonResultsWidget(QWidget):
    """
    Dedicated Accuracy Results Screen shown when a learner completes a lesson.
    Styled consistently with SenyaSabi's quiz results screen (scores_bg.png,
    warm amber/cream/brown palette, circular accuracy ring, and Back to Lessons button).
    """
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(1920, 1080)
        self.setObjectName("lessonResultsWidget")
        self.hide()

        self.bg_label = QLabel(self)
        self.bg_label.setGeometry(0, 0, 1920, 1080)
        self.bg_label.setPixmap(QPixmap(str(ROOT / "resources/img/scores_bg.png")))
        self.bg_label.setScaledContents(True)

        self.btn_close = QPushButton(self)
        self.btn_close.setGeometry(1810, 30, 60, 60)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        close_icon_path = str(ROOT / "resources/img/ui/close_btn.png").replace("\\", "/")
        self.btn_close.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; border-image: url({close_icon_path}) 0 0 0 0 stretch stretch; }} "
            "QPushButton:hover { transform: scale(1.1); }"
        )
        self.btn_close.clicked.connect(self.back_requested.emit)

        # Covers baked 'Excellent!' inside the yellow blob (x: 176..1164, y: 331..511)
        self.title_banner = QLabel("Lesson Completed!", self)
        self.title_banner.setGeometry(160, 310, 1020, 180)
        self.title_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_banner.setStyleSheet(
            "QLabel {"
            "  background-color: #FFDE59;"
            "  color: #704833;"
            "  font-family: 'Cherry Bomb One', 'Segoe UI', sans-serif;"
            "  font-size: 82px;"
            "  font-weight: bold;"
            "}"
        )

        # Lesson Name subtitle neatly centered inside the lower half of the yellow blob
        self.lbl_lesson_name = QLabel("FSL Lesson", self)
        self.lbl_lesson_name.setGeometry(160, 480, 1020, 65)
        self.lbl_lesson_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_lesson_name.setStyleSheet(
            "QLabel {"
            "  background-color: #FFDE59;"
            "  font-family: 'Segoe UI', sans-serif;"
            "  font-size: 32px;"
            "  font-weight: 800;"
            "  color: #704833;"
            "}"
        )

        # Aligned directly next to baked 'Score:' in scores_bg.png (y: 682..748)
        self.lbl_score_val = QLabel("100%", self)
        self.lbl_score_val.setGeometry(475, 640, 260, 140)
        self.lbl_score_val.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_score_val.setStyleSheet(
            "QLabel {"
            "  font-family: 'Cherry Bomb One', 'Segoe UI', sans-serif;"
            "  font-size: 80px;"
            "  font-weight: bold;"
            "  color: #704833;"
            "  background: transparent;"
            "}"
        )

        self.badge_acc = QLabel("100% Accuracy", self)
        self.badge_acc.setGeometry(730, 676, 240, 68)
        self.badge_acc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge_acc.setStyleSheet(
            "QLabel {"
            "  font-family: 'Segoe UI', sans-serif;"
            "  font-size: 24px;"
            "  font-weight: 700;"
            "  color: #2D4014;"
            "  background-color: #BFD379;"
            "  border-radius: 34px;"
            "}"
        )

        self.gauge = _CircularAccuracyGauge(self)
        self.gauge.move(1000, 625)

        self.lbl_message = QLabel(
            "Wonderful job practicing your signs! Keep up the great momentum!",
            self,
        )
        self.lbl_message.setGeometry(170, 795, 980, 72)
        self.lbl_message.setWordWrap(True)
        self.lbl_message.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_message.setStyleSheet(
            "QLabel {"
            "  font-family: 'Segoe UI', sans-serif;"
            "  font-size: 23px;"
            "  font-weight: 700;"
            "  color: #5C3B28;"
            "  background-color: rgba(255, 248, 225, 220);"
            "  border: 2px solid #E2D9C8;"
            "  border-radius: 24px;"
            "  padding: 8px 24px;"
            "}"
        )

        self.btn_back = QPushButton("Back to Lessons", self)
        self.btn_back.setGeometry(170, 890, 380, 85)
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.setStyleSheet(
            "QPushButton {"
            "  background-color: #8C9F3E;"
            "  color: #FFFFFF;"
            "  font-family: 'Segoe UI', sans-serif;"
            "  font-size: 30px;"
            "  font-weight: 700;"
            "  border-radius: 42px;"
            "  border: none;"
            "}"
            "QPushButton:hover { background-color: #9DB446; }"
            "QPushButton:pressed { background-color: #788934; }"
        )
        self.btn_back.clicked.connect(self.back_requested.emit)

    def show_results(
        self,
        lesson_name: str,
        accuracy_pct: int | float,
        completed_count: int | None = None,
        total_count: int | None = None,
        message: str | None = None,
    ):
        try:
            import math
            val = float(accuracy_pct) if accuracy_pct is not None else 0.0
            if not math.isfinite(val):
                val = 0.0
        except Exception:
            val = 0.0
        pct = max(0, min(100, int(round(val))))

        clean_name = str(lesson_name or "Lesson").strip()
        self.lbl_lesson_name.setText(clean_name)

        if completed_count is not None and total_count is not None and total_count > 0:
            self.lbl_score_val.setText(f"{completed_count}/{total_count}")
        else:
            self.lbl_score_val.setText(f"{pct}%")

        self.badge_acc.setText(f"{pct}% Accuracy")
        self.gauge.set_percent(pct)

        if pct >= 85:
            default_msg = "You are a natural! Amazing sign recognition accuracy in this lesson!"
            self.badge_acc.setStyleSheet(
                "QLabel { font-family: 'Segoe UI', sans-serif; font-size: 24px; font-weight: 700; color: #2D4014; background-color: #BFD379; border-radius: 33px; }"
            )
        elif pct >= 60:
            default_msg = "Great effort! Keep practicing these signs to build even stronger fluency!"
            self.badge_acc.setStyleSheet(
                "QLabel { font-family: 'Segoe UI', sans-serif; font-size: 24px; font-weight: 700; color: #5C3B28; background-color: #FFDE59; border-radius: 33px; }"
            )
        else:
            default_msg = "Good start completing this lesson! Practice the signs again anytime to boost your accuracy!"
            self.badge_acc.setStyleSheet(
                "QLabel { font-family: 'Segoe UI', sans-serif; font-size: 24px; font-weight: 700; color: #5C3B28; background-color: #FFE082; border: 2px solid #FFAE00; border-radius: 33px; }"
            )

        self.lbl_message.setText(message or default_msg)
        self.show()
        self.raise_()


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
        self.logo.setFixedSize(176, 60)
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
        self.bg_label.setObjectName("imgBackground")
        self.bg_label.setGeometry(0, 0, 1920, 1080)
        self.bg_label.setStyleSheet("background-color: #C2D076;")

        # Header
        self.header = LessonHeader(self)
        self.header.setGeometry(0, 0, 1920, 90)
        self.header.back_requested.connect(self.back_requested.emit)
        self.header.close_requested.connect(self.close_requested.emit)
        self.btn_back = self.header.btn_back

        # Main Cream Card Container
        self.card = QWidget(self)
        self.card.setGeometry(50, 95, 1820, 935)
        self.card.setStyleSheet("QWidget { background-color: #FAFFDC; border-radius: 40px; }")

        # Target Word / Sign Header Area (above avatar_card)
        self.target_header = QWidget(self.card)
        self.target_header.setGeometry(90, 20, 700, 85)
        self.target_header.setStyleSheet("background: transparent;")
        th_layout = QHBoxLayout(self.target_header)
        th_layout.setContentsMargins(0, 0, 0, 0)

        left_col = QVBoxLayout()
        left_col.setContentsMargins(0, 0, 0, 0)
        left_col.setSpacing(2)

        self.lbl_target_sub = QLabel("SIGN THIS WORD", self.target_header)
        self.lbl_target_sub.setStyleSheet("color: #7A6045; font-size: 13px; font-weight: 700; letter-spacing: 2px;")
        left_col.addWidget(self.lbl_target_sub)

        self.lbl_target_word = QLabel("WORD", self.target_header)
        self.lbl_target_word.setStyleSheet("color: #2F4858; font-size: 34px; font-weight: 800;")
        left_col.addWidget(self.lbl_target_word)
        th_layout.addLayout(left_col, 1)

        self.lbl_progress = QLabel("Word 1 of 5", self.target_header)
        self.lbl_progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_progress.setFixedHeight(38)
        self.lbl_progress.setStyleSheet(
            "background-color: #FFF7D6; color: #69452F; border: 2px solid #D5C79C; "
            "border-radius: 19px; padding: 0 18px; font-size: 14px; font-weight: 700;"
        )
        th_layout.addWidget(self.lbl_progress, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Live Prediction / Detection Pill (above camera_container)
        self.pred_container = QWidget(self.card)
        self.pred_container.setGeometry(970, 30, 760, 65)
        self.pred_container.setStyleSheet("background: transparent;")
        pred_layout = QHBoxLayout(self.pred_container)
        pred_layout.setContentsMargins(0, 0, 0, 0)
        pred_layout.addStretch()

        self.lbl_prediction = QLabel("Waiting for hand...", self.pred_container)
        self.lbl_prediction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_prediction.setFixedHeight(44)
        self.lbl_prediction.setStyleSheet(
            "background-color: #2F4858; color: #E5E7EB; border: 2px solid #5A7385; "
            "border-radius: 22px; padding: 0 24px; font-size: 15px; font-weight: 700;"
        )
        pred_layout.addWidget(self.lbl_prediction)


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
        class _CameraContainer(QWidget):
            def resizeEvent(sub_self, ev):
                super().resizeEvent(ev)
                if hasattr(self, "feedback_overlay") and self.feedback_overlay:
                    self.feedback_overlay.setGeometry(sub_self.rect())
        self.camera_container = _CameraContainer(self.card)
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

        # Dedicated Lesson Accuracy Results Screen Overlay (shown on lesson completion)
        self.results_widget = LessonResultsWidget(self)
        self.results_widget.setGeometry(0, 0, 1920, 1080)
        self.results_widget.hide()
        self.results_widget.back_requested.connect(self.back_requested.emit)


    def set_target(self, word: str, category: str = "SIGN THIS WORD", progress: str = ""):
        self.lbl_target_word.setText(str(word).upper())
        self.lbl_target_sub.setText(str(category).upper())
        if progress:
            self.lbl_progress.setText(str(progress))
            self.lbl_progress.show()
        else:
            self.lbl_progress.hide()

    def set_prediction(self, text: str, status: str = "waiting"):
        self.lbl_prediction.setText(text)
        if status == "correct" or status == "holding":
            self.lbl_prediction.setStyleSheet(
                "background-color: #1E3A2F; color: #5ECF8A; border: 2px solid #5ECF8A; "
                "border-radius: 22px; padding: 0 24px; font-size: 15px; font-weight: 700;"
            )
        elif status == "seeing":
            self.lbl_prediction.setStyleSheet(
                "background-color: #2F4858; color: #FFFFFF; border: 2px solid #F9BD49; "
                "border-radius: 22px; padding: 0 24px; font-size: 15px; font-weight: 700;"
            )
        elif status == "wrong":
            self.lbl_prediction.setStyleSheet(
                "background-color: #3D2222; color: #F87171; border: 2px solid #EF4444; "
                "border-radius: 22px; padding: 0 24px; font-size: 15px; font-weight: 700;"
            )
        else:
            self.lbl_prediction.setStyleSheet(
                "background-color: #2F4858; color: #C5CCD3; border: 2px solid #5A7385; "
                "border-radius: 22px; padding: 0 24px; font-size: 15px; font-weight: 700;"
            )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "bg_label") and self.bg_label:
            self.bg_label.setGeometry(self.rect())

    def set_camera_active(self, active: bool):
        icon_name = "btn_cam_off.png" if active else "btn_cam_on.png"
        path = str(ROOT / "resources/img/ui" / icon_name).replace("\\", "/")
        self.btn_cam.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; border-image: url({path}) 0 0 0 0 stretch stretch; }} "
            "QPushButton:hover { transform: scale(1.08); }"
        )
