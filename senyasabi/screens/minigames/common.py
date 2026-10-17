"""Shared responsive widgets and round controls for the three minigames."""
import math
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
                              QScrollArea, QGridLayout, QLineEdit, QApplication)
from backend.minigame_service import ROOT, CONFIG, GameSession


def style(widget, name):
    widget.setProperty("class", name)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()
    return widget


def label(text, name):
    widget = QLabel(text)
    widget.setTextFormat(Qt.TextFormat.PlainText)
    widget.setWordWrap(True)
    return style(widget, name)


def button(text, action, name="controlButton"):
    widget = style(QPushButton(text), name)
    widget.clicked.connect(action)
    return widget


class GameCanvas(QWidget):
    """Own layouts replace the legacy absolute-form scaling hook."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._fitted_form = self
        self.resize(1100, 760)
        self.setStyleSheet((ROOT / "resources/styles/minigames.qss").read_text())

    def fit(self):
        if self.layout():
            self.layout().activate()


class SignImage(QLabel):
    def __init__(self, letter, size=120):
        super().__init__()
        style(self, "signImageCard")
        self.source = QPixmap(str(ROOT / "resources/VRM_SIGNS" / f"{letter}.png"))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(size, size)
        self.refresh()

    def refresh(self):
        if self.source.isNull():
            self.setText("Sign image unavailable")
        else:
            self.setPixmap(self.source.scaled(max(1,self.width()-20), max(1,self.height()-20),
                Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.refresh()


class GameWindow(GameCanvas):
    back_requested = Signal()

    def __init__(self, kind, parent=None, module_code=None):
        super().__init__(parent)
        self.kind = kind
        self.setObjectName("minigameScreen")
        self.module_code = module_code
        self.session = GameSession(kind, module_code=module_code)
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(26, 18, 26, 18)
        header = QHBoxLayout()
        header.addWidget(button("Back", self.go_back, "secondaryButton"))
        header.addWidget(label(CONFIG[kind][0], "gameTitle"), 1)
        self.timer_label = label("", "timer")
        self.score_label = label("", "score")
        header.addWidget(self.timer_label)
        header.addWidget(self.score_label)
        self.body.addLayout(header)
        self.body.addWidget(label(CONFIG[kind][1], "gameSubtitle"))
        self.content = QVBoxLayout()
        self.body.addLayout(self.content, 1)
        self.feedback = label("", "resultCard")
        self.feedback.hide()
        self.body.addWidget(self.feedback)
        self.next_button = button("Next", self.next_round, "primaryButton")
        self.next_button.setEnabled(False)
        self.body.addWidget(self.next_button)
        self.countdown = QTimer(self)
        self.countdown.setInterval(100)
        self.countdown.timeout.connect(self.tick)
        QApplication.instance().aboutToQuit.connect(self.stop)

    def start(self):
        self.render_round()
        self.tick()
        if self.session.saved_time is None:
            self.countdown.start()

    def tick(self):
        self.timer_label.setText(f"Time: {math.ceil(self.session.remaining)}s")
        warning = self.session.remaining <= 10
        if self.timer_label.property("warning") != warning:
            self.timer_label.setProperty("warning", warning)
            style(self.timer_label, "timer")
        if self.session.remaining <= 0 and not self.session.resolved:
            self.resolve(False)

    def resolve(self, correct):
        if not self.session.finish(correct):
            return
        self.countdown.stop()
        self.stop_activity()
        self.feedback.setText(("Correct!" if correct else "Round over.") + f" Answer: {self.session.word}")
        self.feedback.show()
        self.next_button.setEnabled(True)
        self.score_label.setText(f"Score: {self.session.score}/{self.session.total}")

    def next_round(self):
        if not self.session.resolved:
            return
        if self.session.next_round():
            self.feedback.hide()
            self.next_button.setEnabled(False)
            self.start()
        else:
            self.stop()
            self.feedback.setText(f"Game complete! Score: {self.session.score}/{self.session.total}")
            self.feedback.show()
            self.next_button.setEnabled(False)

    def round_header(self):
        self.score_label.setText(f"Round {self.session.index+1}/{self.session.total} | Score {self.session.score}")

    def stop_activity(self):
        pass

    def stop(self):
        self.countdown.stop()
        self.stop_activity()

    def go_back(self):
        self.stop()
        self.back_requested.emit()

    def hideEvent(self, event):
        self.stop()
        super().hideEvent(event)

    def closeEvent(self, event):
        self.stop()
        super().closeEvent(event)


class AnswerGame(GameWindow):
    def __init__(self, kind, parent=None, module_code=None):
        super().__init__(kind, parent, module_code=module_code)
        self.answer = QLineEdit()
        self.answer.setPlaceholderText("Type the word or phrase, preserving spaces/apostrophes")
        self.submit = button("Check answer", self.check_answer, "primaryButton")
        self.answer.returnPressed.connect(self.check_answer)
        self.body.insertWidget(self.body.count()-2, self.answer)
        self.body.insertWidget(self.body.count()-2, self.submit)

    def check_answer(self):
        if self.session.resolved or self.session.saved_time is not None:
            return
        if self.session.remaining <= 0:
            self.resolve(False)
        elif self.session.check_answer(self.answer.text()):
            self.resolve(True)
        else:
            self.feedback.setText("Try again before time runs out.")
            self.feedback.show()

    def round_header(self):
        super().round_header()
        self.answer.clear()
        self.answer.setEnabled(True)
        self.submit.setEnabled(True)

    def resolve(self, correct):
        super().resolve(correct)
        self.answer.setEnabled(False)
        self.submit.setEnabled(False)
