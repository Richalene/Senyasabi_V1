"""Offline identification quiz; vocabulary is supplied only by quiz_service."""
from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QGridLayout, QWidget, QScrollArea, QLineEdit
from backend.quiz_service import QuizSession
from screens.minigames.common import GameCanvas, SignImage, label, button
from screens.media_player import SignVideoPlayer
from screens.navigation import BackButton, install_page_menu


class ModuleQuiz(GameCanvas):
    back_requested = Signal()

    def __init__(self, module_code):
        super().__init__()
        self.module_code = module_code
        self.session = QuizSession(module_code)
        layout = QVBoxLayout(self)
        self.back_button = BackButton()
        self.back_button.clicked.connect(self.back_requested.emit)
        navigation_row = QHBoxLayout()
        navigation_row.addWidget(self.back_button, alignment=Qt.AlignmentFlag.AlignLeft)
        navigation_row.addStretch()
        navigation_row.addSpacing(76)
        layout.addLayout(navigation_row)
        layout.addWidget(label(self.session.definition.title, "gameTitle"))
        self.notice = label("Fingerspelling quiz: decode the letters to find this module’s word or phrase.", "instructionCard")
        self.notice.setWordWrap(True)
        layout.addWidget(self.notice)
        self.progress = label("", "gameSubtitle")
        layout.addWidget(self.progress)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        layout.addWidget(self.scroll, 1)
        self.video = SignVideoPlayer(self)
        self.video.setMaximumHeight(210)
        layout.addWidget(self.video)
        self.answer = QLineEdit()
        self.answer.setPlaceholderText("Type the decoded answer")
        self.answer.returnPressed.connect(self.submit)
        layout.addWidget(self.answer)
        self.feedback = label("", "resultCard")
        self.feedback.setWordWrap(True)
        layout.addWidget(self.feedback)
        self.check_button = button("Check answer", self.submit, "primaryButton")
        layout.addWidget(self.check_button)
        self.next_button = button("Next", self.next_question, "secondaryButton")
        layout.addWidget(self.next_button)
        self.render()
        install_page_menu(self)

    def render(self):
        self.next_button.setEnabled(False)
        self.feedback.clear()
        self.feedback.hide()
        self.answer.clear()
        self.answer.setEnabled(not self.session.complete)
        self.check_button.setEnabled(not self.session.complete)
        if self.session.complete:
            self.video.stop()
            self.scroll.hide()
            self.video.hide()
            self.progress.setText(f"Quiz complete: {self.session.score}/{len(self.session.questions)} ({self.session.percent}%)")
            self.feedback.setText("Passed!" if self.session.percent >= self.session.definition.passing_score else "Keep practicing and try again.")
            self.feedback.show()
            return
        self.progress.setText(f"Question {self.session.index+1}/{len(self.session.questions)}")
        self.render_sequence(force=True)
        self.video.set_sign(self.module_code, self.session.current.sign_code)

    def render_sequence(self, force=False):
        if self.session.complete:
            return
        columns = max(1, min(7, self.scroll.viewport().width()//105))
        if not force and getattr(self, '_sequence_columns', None) == columns:
            return
        self._sequence_columns = columns
        old = self.scroll.takeWidget()
        if old:
            old.deleteLater()
        canvas = QWidget()
        grid = QGridLayout(canvas)
        grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        row, col = 0, 0
        for char in self.session.current.label.upper():
            if char == " ":
                row, col = row+1, 0
            elif "A" <= char <= "Z":
                grid.addWidget(SignImage(char, 95), row, col)
                col += 1
                if col == columns:
                    row, col = row+1, 0
        self.scroll.setWidget(canvas)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'scroll'):
            QTimer.singleShot(0, self.reflow_sequence)

    def reflow_sequence(self):
        self.render_sequence()

    def submit(self):
        if self.session.complete or self.session.answered:
            return
        correct = self.session.answer(self.answer.text())
        self.feedback.setText(("Correct!" if correct else "Try this one again in practice.") + f" Answer: {self.session.current.label}")
        self.feedback.show()
        self.answer.setEnabled(False)
        self.check_button.setEnabled(False)
        self.next_button.setEnabled(True)

    def next_question(self):
        self.session.advance()
        self.render()

    def hideEvent(self, event):
        self.video.stop()
        super().hideEvent(event)
