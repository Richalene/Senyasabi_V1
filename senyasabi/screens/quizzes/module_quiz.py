"""
Polished Figma-quality Module Quiz screen redesigned to match SenyaSabi styling.
Supports both visual video/sign reference, interactive choice selection,
responsive fingerspell reflow, and comprehensive score reporting.
"""
from __future__ import annotations

from pathlib import Path
import random

from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QScrollArea, QLineEdit, QSizePolicy
)

from backend.quiz_service import QuizSession
from backend.content_service import get_signs_for_module
from screens.minigames.common import GameCanvas, ROOT
from screens.media_player import SignVideoPlayer
from screens.navigation import BackButton, install_page_menu
from screens.minigames.minigame_ui_components import MinigameHeader, MinigameScoreWidget
from screens.startup import FittedForm
from backend.media_service import warm_alphabet_stills, alphabet_still, _cached_path

class QuizRetryWidget(QWidget):
    """
    Encouraging quiz retry overlay shown when a learner scores below 75%.
    Matches SenyaSabi's warm cream/amber/brown visual styling.
    """
    retry_requested = Signal()
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(1920, 1080)
        self.setObjectName("quizRetryWidget")

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

        self.title_banner = QLabel("Not Quite Yet!", self)
        self.title_banner.setGeometry(160, 310, 1020, 220)
        self.title_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_banner.setStyleSheet(
            "QLabel {"
            "  background-color: #FFDE59;"
            "  color: #704833;"
            "  font-family: 'Cherry Bomb One', 'Segoe UI', sans-serif;"
            "  font-size: 92px;"
            "  font-weight: bold;"
            "}"
        )

        # Aligned directly next to baked 'Score:' in scores_bg.png (y: 682..748)
        self.lbl_score_val = QLabel("0/5", self)
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

        self.badge_acc = QLabel("0% Score", self)
        self.badge_acc.setGeometry(740, 665, 230, 68)
        self.badge_acc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge_acc.setStyleSheet(
            "QLabel {"
            "  font-family: 'Segoe UI', sans-serif;"
            "  font-size: 24px;"
            "  font-weight: 700;"
            "  color: #5C3B28;"
            "  background-color: #FFE082;"
            "  border: 2.5px solid #FFAE00;"
            "  border-radius: 34px;"
            "}"
        )

        self.lbl_message = QLabel(
            "You need at least 75% to pass. Review the signs and try again!",
            self,
        )
        self.lbl_message.setGeometry(165, 785, 960, 75)
        self.lbl_message.setWordWrap(True)
        self.lbl_message.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_message.setStyleSheet(
            "QLabel {"
            "  font-family: 'Segoe UI', sans-serif;"
            "  font-size: 24px;"
            "  font-weight: 700;"
            "  color: #5C3B28;"
            "  background-color: rgba(255, 248, 225, 220);"
            "  border: 2px solid #E2D9C8;"
            "  border-radius: 24px;"
            "  padding: 8px 24px;"
            "}"
        )

        self.btn_retry = QPushButton("Try Again", self)
        self.btn_retry.setGeometry(170, 885, 340, 85)
        self.btn_retry.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_retry.setStyleSheet(
            "QPushButton {"
            "  background-color: #FFAE00;"
            "  color: #5C3B28;"
            "  font-family: 'Segoe UI', sans-serif;"
            "  font-size: 30px;"
            "  font-weight: 700;"
            "  border-radius: 42px;"
            "  border: none;"
            "}"
            "QPushButton:hover { background-color: #FFBE33; }"
            "QPushButton:pressed { background-color: #E69D00; }"
        )
        self.btn_retry.clicked.connect(self.retry_requested.emit)

        self.btn_back = QPushButton("Back to Lessons", self)
        self.btn_back.setGeometry(540, 885, 340, 85)
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.setStyleSheet(
            "QPushButton {"
            "  background-color: #FFFDF0;"
            "  color: #704833;"
            "  font-family: 'Segoe UI', sans-serif;"
            "  font-size: 26px;"
            "  font-weight: 700;"
            "  border-radius: 42px;"
            "  border: 3.5px solid #D5C9A9;"
            "}"
            "QPushButton:hover { background-color: #FFF8E7; border-color: #B8A783; }"
            "QPushButton:pressed { background-color: #F5ECCE; }"
        )
        self.btn_back.clicked.connect(self.back_requested.emit)

    def set_score(self, score: int, total: int, percent: int | None = None):
        pct = round(100 * score / total) if (percent is None and total > 0) else (percent or 0)
        self.lbl_score_val.setText(f"{score}/{total}")
        self.badge_acc.setText(f"{int(pct)}%")


class ModuleQuiz(GameCanvas):
    back_requested = Signal()

    def __init__(self, module_code: str, parent=None):
        warm_alphabet_stills()
        super().__init__(parent)
        self.resize(1920, 1080)
        self.module_code = module_code.casefold() if module_code else "greeting"
        self.session = QuizSession(self.module_code)

        # Background foliage
        self.bg_label = QLabel(self)
        self.bg_label.setObjectName("imgBackground")
        self.bg_label.setGeometry(0, 0, 1920, 1080)
        self.bg_label.setStyleSheet("background-color: #C2D076;")

        # Header
        self.header = MinigameHeader(self)
        self.header.setGeometry(0, 0, 1920, 90)
        self.header.close_requested.connect(self.back_requested.emit)

        self.back_button = BackButton(self)
        self.back_button.setGeometry(40, 20, 50, 50)
        self.back_button.clicked.connect(self.back_requested.emit)

        # Main Cream Container Card
        self.card = QWidget(self)
        self.card.setGeometry(50, 95, 1820, 935)
        self.card.setStyleSheet("QWidget#quizMainCard { background-color: #FAFFDC; border-radius: 40px; }")
        self.card.setObjectName("quizMainCard")

        # Top Info inside Card
        self.title_lbl = QLabel(self.card)
        self.title_lbl.setGeometry(80, 30, 950, 48)
        self.title_lbl.setStyleSheet(
            "font-family: 'Segoe UI', sans-serif; font-size: 32px; font-weight: 800; color: #5C3B28; background: transparent;"
        )
        self.title_lbl.setText(self.session.definition.title.upper())

        self.notice = QLabel(self.card)
        self.notice.setGeometry(80, 80, 950, 35)
        self.notice.setStyleSheet(
            "font-family: 'Segoe UI', sans-serif; font-size: 18px; font-style: italic; color: #8F8C78; background: transparent;"
        )
        self.notice.setText("Watch the sign and identify the correct word or phrase.")
        self.notice.setWordWrap(True)

        self.progress = QLabel(self.card)
        self.progress.setGeometry(1510, 35, 230, 48)
        self.progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress.setStyleSheet(
            "background-color: #2F4858; color: #E5E7EB; border: 2px solid #5A7385; "
            "border-radius: 24px; padding: 0 20px; font-size: 16px; font-weight: 700;"
        )

        # Left Column: Visual Sign Card
        self.left_card = QWidget(self.card)
        self.left_card.setGeometry(80, 130, 820, 755)
        self.left_card.setStyleSheet("background-color: #F9BD49; border-radius: 35px;")

        left_layout = QVBoxLayout(self.left_card)
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(15)

        # Visual Media: Video Player
        self.video = SignVideoPlayer(self.left_card, muted=True, aspect_ratio_mode=Qt.AspectRatioMode.KeepAspectRatioByExpanding)
        self.video.setMinimumHeight(300)
        left_layout.addWidget(self.video, 1)

        # Visual Media: Static Sign Image fallback when video is unavailable
        self.sign_image = QLabel(self.left_card)
        self.sign_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sign_image.setStyleSheet("background: transparent;")
        self.sign_image.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.sign_image.hide()
        left_layout.addWidget(self.sign_image, 1)
        self._current_sign_pixmap = None

        # Right Column: Answer Interface
        self.right_card = QWidget(self.card)
        self.right_card.setGeometry(940, 130, 800, 755)
        self.right_card.setStyleSheet("background: transparent;")

        right_layout = QVBoxLayout(self.right_card)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(16)

        # Section 1: Multiple Choice Options
        self.lbl_choice_prompt = QLabel("Select the correct answer:", self.right_card)
        self.lbl_choice_prompt.setStyleSheet(
            "font-family: 'Segoe UI', sans-serif; font-size: 22px; font-weight: 700; color: #5C3B28; background: transparent;"
        )
        right_layout.addWidget(self.lbl_choice_prompt)

        self.choice_grid = QGridLayout()
        self.choice_grid.setSpacing(14)
        self.choice_buttons: list[QPushButton] = []
        for i in range(4):
            btn = QPushButton(f"Option {i + 1}", self.right_card)
            btn.setFixedHeight(66)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                "QPushButton {"
                "  background-color: #FFFFFF;"
                "  color: #5C3B28;"
                "  font-family: 'Segoe UI', sans-serif;"
                "  font-size: 20px;"
                "  font-weight: 700;"
                "  border: 3px solid #E2D9C8;"
                "  border-radius: 20px;"
                "  padding: 0 20px;"
                "  text-align: left;"
                "}"
                "QPushButton:hover {"
                "  background-color: #FFF3D6;"
                "  border-color: #FFAE00;"
                "}"
            )
            btn.clicked.connect(lambda checked=False, b=btn: self._on_choice_clicked(b))
            self.choice_buttons.append(btn)
            self.choice_grid.addWidget(btn, i // 2, i % 2)
        right_layout.addLayout(self.choice_grid)

        # Section 2: Or Type Answer
        self.lbl_or_type = QLabel("Or type your answer below:", self.right_card)
        self.lbl_or_type.setStyleSheet(
            "font-family: 'Segoe UI', sans-serif; font-size: 17px; font-style: italic; color: #8F8C78; background: transparent;"
        )
        right_layout.addWidget(self.lbl_or_type)

        self.answer = QLineEdit(self.right_card)
        self.answer.setFixedHeight(60)
        self.answer.setPlaceholderText("Type your answer here")
        self.answer.setStyleSheet(
            "QLineEdit {"
            "  background-color: #FFFFFF;"
            "  color: #5C3B28;"
            "  font-family: 'Segoe UI', sans-serif;"
            "  font-size: 22px;"
            "  font-weight: 700;"
            "  border: 3px solid #D5C9A9;"
            "  border-radius: 30px;"
            "  padding: 0 24px;"
            "}"
            "QLineEdit:focus {"
            "  border-color: #FFAE00;"
            "}"
        )
        self.answer.returnPressed.connect(self.submit)
        self.answer.textChanged.connect(self._sync_choice_highlight)
        right_layout.addWidget(self.answer)

        # Feedback Banner
        self.feedback = QLabel(self.right_card)
        self.feedback.setWordWrap(True)
        self.feedback.setMinimumHeight(60)
        self.feedback.hide()
        right_layout.addWidget(self.feedback)

        right_layout.addStretch()

        # Action Buttons Row
        actions_row = QHBoxLayout()
        actions_row.setSpacing(20)

        self.check_button = QPushButton("Check Answer", self.right_card)
        self.check_button.setFixedHeight(62)
        self.check_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.check_button.setStyleSheet(
            "QPushButton {"
            "  background-color: #FFAE00;"
            "  color: #5C3B28;"
            "  font-family: 'Segoe UI', sans-serif;"
            "  font-size: 22px;"
            "  font-weight: 700;"
            "  border-radius: 31px;"
            "  border: none;"
            "}"
            "QPushButton:hover { background-color: #FFBE33; }"
            "QPushButton:pressed { background-color: #E69D00; }"
            "QPushButton:disabled { background-color: #E0DACB; color: #9C9482; }"
        )
        self.check_button.clicked.connect(self.submit)
        actions_row.addWidget(self.check_button, 1)

        self.next_button = QPushButton("Next Question  ➔", self.right_card)
        self.next_button.setFixedHeight(62)
        self.next_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_button.setStyleSheet(
            "QPushButton {"
            "  background-color: #ACC412;"
            "  color: #FFFFFF;"
            "  font-family: 'Segoe UI', sans-serif;"
            "  font-size: 22px;"
            "  font-weight: 700;"
            "  border-radius: 31px;"
            "  border: none;"
            "}"
            "QPushButton:hover { background-color: #BFDA16; }"
            "QPushButton:pressed { background-color: #96AB10; }"
            "QPushButton:disabled { background-color: #D2D2D2; color: #949494; }"
        )
        self.next_button.clicked.connect(self.next_question)
        self.next_button.setEnabled(False)
        actions_row.addWidget(self.next_button, 1)

        right_layout.addLayout(actions_row)

        # End of Game Score Screen overlay
        self.score_widget = MinigameScoreWidget(self)
        self.score_widget.setGeometry(0, 0, 1920, 1080)
        self.score_widget.hide()
        self.score_widget.continue_requested.connect(self.back_requested.emit)
        self.score_widget.close_requested.connect(self.back_requested.emit)
        self.score_widget.replay_requested.connect(self.restart_quiz)

        # Retry Screen overlay (shown when score < 75%)
        self.retry_widget = QuizRetryWidget(self)
        self.retry_widget.setGeometry(0, 0, 1920, 1080)
        self.retry_widget.hide()
        self.retry_widget.retry_requested.connect(self.restart_quiz)
        self.retry_widget.back_requested.connect(self.back_requested.emit)

        self._fitted_form = FittedForm(self)
        self.render()
        install_page_menu(self)

    def _on_choice_clicked(self, clicked_btn: QPushButton):
        if self.session.complete or self.session.answered:
            return
        text = clicked_btn.text().strip()
        self.answer.setText(text)
        self._sync_choice_highlight(text)

    def _sync_choice_highlight(self, text: str):
        normalized = text.strip().upper()
        for btn in self.choice_buttons:
            if btn.text().strip().upper() == normalized and normalized:
                btn.setStyleSheet(
                    "QPushButton {"
                    "  background-color: #FFE082;"
                    "  color: #704833;"
                    "  font-family: 'Segoe UI', sans-serif;"
                    "  font-size: 20px;"
                    "  font-weight: 700;"
                    "  border: 3.5px solid #FFAE00;"
                    "  border-radius: 20px;"
                    "  padding: 0 20px;"
                    "  text-align: left;"
                    "}"
                )
            else:
                btn.setStyleSheet(
                    "QPushButton {"
                    "  background-color: #FFFFFF;"
                    "  color: #5C3B28;"
                    "  font-family: 'Segoe UI', sans-serif;"
                    "  font-size: 20px;"
                    "  font-weight: 700;"
                    "  border: 3px solid #E2D9C8;"
                    "  border-radius: 20px;"
                    "  padding: 0 20px;"
                    "  text-align: left;"
                    "}"
                    "QPushButton:hover {"
                    "  background-color: #FFF3D6;"
                    "  border-color: #FFAE00;"
                    "}"
                )

    def restart_quiz(self):
        self.session = QuizSession(self.module_code)
        self.score_widget.hide()
        self.retry_widget.hide()
        self.card.show()
        self.render()

    def render(self):
        self.next_button.setEnabled(False)
        self.feedback.clear()
        self.feedback.hide()
        self.answer.clear()
        self.answer.setEnabled(not self.session.complete)
        self.check_button.setEnabled(not self.session.complete)

        for btn in self.choice_buttons:
            btn.setEnabled(not self.session.complete)

        if self.session.complete:
            self.sign_image.hide()
            self.video.hide()
            self.card.hide()
            total = len(self.session.questions)
            pct = self.session.percent
            if self.session.passed:
                self.retry_widget.hide()
                self.score_widget.set_score(self.session.score, total)
                self.score_widget.show()
            else:
                self.score_widget.hide()
                self.retry_widget.set_score(self.session.score, total, pct)
                self.retry_widget.show()
            self._record_progress()
            return

        self.card.show()
        self.score_widget.hide()
        self.retry_widget.hide()
        total_q = len(self.session.questions)
        self.progress.setText(f"Question {self.session.index + 1} of {total_q}")

        # Setup 4 options: 1 correct + 3 distractors
        current_sign = self.session.current
        correct_label = current_sign.label if current_sign else ""

        all_signs = get_signs_for_module(self.module_code)
        distractors = [s.label for s in all_signs if s.label.upper() != correct_label.upper()]
        random.shuffle(distractors)
        choices = [correct_label] + distractors[:3]
        while len(choices) < 4:
            choices.append(f"Sign {len(choices) + 1}")
        random.shuffle(choices)

        for btn, ch in zip(self.choice_buttons, choices):
            btn.setText(ch)
        self._sync_choice_highlight("")

        # Visual Media: Show sign video or fallback to static sign image
        if current_sign:
            try:
                sign_module = getattr(current_sign, "module_code", None) or self.module_code
                self.video.set_sign(sign_module, current_sign.sign_code)
                if self.video.media and self.video.media.available:
                    self.sign_image.hide()
                    self.video.show()
                    self._play_token = getattr(self, "_play_token", 0) + 1
                    if self.isVisible():
                        self.video.play()
                    else:
                        token = self._play_token
                        QTimer.singleShot(0, lambda t=token: self._play_if_ready(t))
                else:
                    self.video.hide()
                    self._show_sign_image(current_sign)
            except Exception:
                self.video.hide()
                self._show_sign_image(current_sign)
        else:
            self.video.hide()
            self._show_sign_image(None)

    def _resolve_sign_pixmap(self, sign) -> QPixmap | None:
        if not sign:
            return None
        candidates = []
        if getattr(sign, "sign_code", None):
            candidates.append(str(sign.sign_code))
        if getattr(sign, "label", None):
            candidates.append(str(sign.label))

        for cand in candidates:
            # 1. Alphabet stills (Supabase cached or bundled VRM letter PNG)
            try:
                still = alphabet_still(cand)
                if still and Path(still).is_file():
                    pm = QPixmap(str(still))
                    if not pm.isNull():
                        return pm
            except Exception:
                pass

            # 2. Bundled VRM_SIGNS image
            try:
                vrm_path = ROOT / "resources" / "VRM_SIGNS" / f"{cand.upper()}.png"
                if vrm_path.is_file():
                    pm = QPixmap(str(vrm_path))
                    if not pm.isNull():
                        return pm
            except Exception:
                pass

        # 3. Media cache via media_id
        media_id = getattr(sign, "media_id", None)
        if media_id is not None:
            try:
                cached = _cached_path(media_id)
                if cached and Path(cached).is_file():
                    pm = QPixmap(str(cached))
                    if not pm.isNull():
                        return pm
            except Exception:
                pass

        return None

    def _show_sign_image(self, sign):
        self._current_sign_pixmap = self._resolve_sign_pixmap(sign)
        self._update_sign_image_pixmap()
        self.sign_image.show()

    def _update_sign_image_pixmap(self):
        if not hasattr(self, "sign_image") or not self.sign_image:
            return
        pixmap = getattr(self, "_current_sign_pixmap", None)
        if pixmap and not pixmap.isNull():
            size = self.sign_image.size()
            w = max(200, size.width() - 40)
            h = max(200, size.height() - 40)
            scaled = pixmap.scaled(
                w, h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.sign_image.setPixmap(scaled)
            self.sign_image.setText("")
        else:
            self.sign_image.setPixmap(QPixmap())
            self.sign_image.setText("No sign media available")
            self.sign_image.setStyleSheet("color: #8F8C78; font-size: 18px; font-weight: 600; background: transparent;")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "sign_image") and self.sign_image.isVisible():
            QTimer.singleShot(0, self._update_sign_image_pixmap)

    def submit(self):
        if self.session.complete or self.session.answered:
            return
        user_answer = self.answer.text().strip()
        correct = self.session.answer(user_answer)
        target_name = self.session.current.label if self.session.current else ""

        if correct:
            self.feedback.setText(f"✔  Correct! That is '{target_name}'.")
            self.feedback.setStyleSheet(
                "background-color: #EAF8EE; color: #1E3A2F; border: 2.5px solid #5ECF8A; "
                "border-radius: 18px; padding: 12px 24px; font-family: 'Segoe UI', sans-serif; font-size: 20px; font-weight: bold;"
            )
        else:
            self.feedback.setText(f"✖  Not quite! The correct sign is: {target_name}")
            self.feedback.setStyleSheet(
                "background-color: #FDF2F2; color: #8A1F1D; border: 2.5px solid #E53935; "
                "border-radius: 18px; padding: 12px 24px; font-family: 'Segoe UI', sans-serif; font-size: 20px; font-weight: bold;"
            )

        self.feedback.show()
        self.answer.setEnabled(False)
        self.check_button.setEnabled(False)
        for btn in self.choice_buttons:
            btn.setEnabled(False)
        self.next_button.setEnabled(True)

    def next_question(self):
        self.session.advance()
        self.render()

    def _record_progress(self):
        try:
            from backend import auth_service, sync_service, content_service
            user = auth_service.get_current_user()
            if user:
                quiz_id = content_service.get_quiz_id(self.module_code)
                uid = user.get("user_id")
                if uid and uid != "dev-session":
                    import uuid
                    if isinstance(uid, str):
                        try:
                            uid = uuid.UUID(uid)
                        except ValueError:
                            uid = None
                    if uid is not None and quiz_id is not None:
                        from datetime import datetime, timezone
                        now = datetime.now(timezone.utc)
                        sync_service.queue_quiz_attempt(
                            user_id=uid,
                            attempt_id=uuid.uuid4(),
                            quiz_id=quiz_id,
                            started_at=now,
                            completed_at=now,
                            score=self.session.score,
                            max_score=len(self.session.questions),
                            percentage=float(self.session.percent),
                            passed=self.session.passed,
                        )
        except Exception:
            pass

    def showEvent(self, event):
        super().showEvent(event)
        token = getattr(self, "_play_token", 0)
        if token:
            QTimer.singleShot(0, lambda t=token: self._play_if_ready(t))

    def _play_if_ready(self, token: int):
        try:
            from shiboken6 import isValid
            if not isValid(self) or not self.isVisible() or self.session.complete:
                return
            if token != getattr(self, "_play_token", 0):
                return
            if hasattr(self, "video") and self.video is not None and self.video.media and self.video.media.available:
                self.video.play()
        except Exception:
            pass

    def hideEvent(self, event):
        if hasattr(self, "video") and self.video is not None:
            self.video.pause()
        super().hideEvent(event)
