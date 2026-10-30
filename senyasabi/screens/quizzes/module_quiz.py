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
from screens.minigames.common import GameCanvas, SignImage, ROOT
from screens.media_player import SignVideoPlayer
from screens.navigation import BackButton, install_page_menu
from screens.minigames.minigame_ui_components import MinigameHeader, MinigameScoreWidget
from screens.startup import FittedForm


class ModuleQuiz(GameCanvas):
    back_requested = Signal()

    def __init__(self, module_code: str, parent=None):
        super().__init__(parent)
        self.resize(1920, 1080)
        self.module_code = module_code.casefold() if module_code else "greeting"
        self.session = QuizSession(self.module_code)
        self._sequence_columns = 5

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
        self.notice.setText("Fingerspelling quiz: decode the letters or sign to find this module’s word.")
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
        self.video = SignVideoPlayer(self.left_card, muted=True)
        self.video.setMinimumHeight(300)
        left_layout.addWidget(self.video, 1)

        # Visual Media: Scroll Area for Fingerspelling Sign Sequence
        self.scroll = QScrollArea(self.left_card)
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("background: transparent; border: none;")
        left_layout.addWidget(self.scroll, 1)

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
        self.answer.setPlaceholderText("Type the decoded answer")
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
            self.video.stop()
            self.scroll.hide()
            self.video.hide()
            self.card.hide()
            self.score_widget.set_score(self.session.score, len(self.session.questions))
            self.score_widget.show()
            self._record_progress()
            return

        self.card.show()
        self.score_widget.hide()
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

        # Visual Media: Render fingerspell sequence & check video
        self.render_sequence(force=True)
        if current_sign:
            try:
                self.video.set_sign(self.module_code, current_sign.sign_code)
                if self.video.media and self.video.media.available:
                    self.video.show()
                    self.scroll.hide()
                    self.video.play()
                else:
                    self.video.stop()
                    self.video.hide()
                    self.scroll.show()
            except Exception:
                self.video.stop()
                self.video.hide()
                self.scroll.show()

    def render_sequence(self, force=False):
        if self.session.complete:
            return
        columns = max(1, min(7, self.scroll.viewport().width() // 105))
        if not force and getattr(self, "_sequence_columns", None) == columns:
            return
        self._sequence_columns = columns
        old = self.scroll.takeWidget()
        if old:
            old.deleteLater()
        canvas = QWidget()
        grid = QGridLayout(canvas)
        grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        grid.setSpacing(10)
        grid.setContentsMargins(10, 10, 10, 10)
        row, col = 0, 0
        current = self.session.current
        if current and current.label:
            for char in current.label.upper():
                if char == " ":
                    row, col = row + 1, 0
                elif "A" <= char <= "Z":
                    grid.addWidget(SignImage(char, 95), row, col)
                    col += 1
                    if col == columns:
                        row, col = row + 1, 0
        self.scroll.setWidget(canvas)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "scroll"):
            QTimer.singleShot(0, self.reflow_sequence)

    def reflow_sequence(self):
        self.render_sequence()

    def submit(self):
        if self.session.complete or self.session.answered:
            return
        user_answer = self.answer.text().strip()
        correct = self.session.answer(user_answer)
        target_name = self.session.current.label if self.session.current else ""

        if correct:
            self.feedback.setText(f"✔  Correct! You decoded '{target_name}'.")
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
                lesson_id = content_service.get_lesson_id(self.module_code)
                uid = user.get("user_id")
                if uid and uid != "dev-session":
                    import uuid
                    if isinstance(uid, str):
                        try:
                            uid = uuid.UUID(uid)
                        except ValueError:
                            uid = None
                    if uid is not None and lesson_id is not None:
                        from datetime import datetime, timezone
                        now = datetime.now(timezone.utc)
                        sync_service.get_sync_service().queue_quiz_attempt(
                            user_id=uid,
                            attempt_id=uuid.uuid4(),
                            quiz_id=lesson_id,
                            started_at=now,
                            completed_at=now,
                            score=self.session.score,
                            max_score=len(self.session.questions),
                            percentage=float(self.session.percent),
                            passed=(self.session.percent >= self.session.definition.passing_score),
                        )
        except Exception:
            pass

    def hideEvent(self, event):
        if hasattr(self, "video") and self.video is not None:
            self.video.stop()
        super().hideEvent(event)
