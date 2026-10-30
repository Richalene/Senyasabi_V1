class _AnswerProxy:
    def __init__(self, game_view):
        self._gv = game_view
    def setText(self, text):
        clean = "".join(ch.upper() for ch in str(text) if ch.isalnum())
        self._gv.user_input = clean
        self._gv.update_tiles()
    def text(self):
        return self._gv.user_input

"""Sign Detective screen redesigned to match the Figma mockup."""
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QWidget, QLabel, QPushButton, QHBoxLayout,
                              QVBoxLayout, QStackedWidget)
from backend.minigame_service import ROOT, GameSession
from screens.startup import FittedForm
from .minigame_ui_components import (HowToPlayWidget, MinigameScoreWidget,
                                     MinigameHeader, LetterTile, CircularActionButton)


class SignDetectiveCard(QWidget):
    """
    Individual alphabet sign card in Sign Detective:
    Displays the sign corresponding to a letter on a clean white rounded card.
    """
    def __init__(self, letter, parent=None):
        super().__init__(parent)
        self.setFixedSize(130, 130)
        self.letter = letter.upper()
        self.setStyleSheet(
            "SignDetectiveCard {"
            "  background-color: #FFFFFF;"
            "  border: 3px solid #E5DEC6;"
            "  border-radius: 20px;"
            "}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        self.img_label = QLabel(self)
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        path = ROOT / "resources/VRM_SIGNS" / f"{self.letter}.png"
        if path.exists():
            self.img_label.setPixmap(QPixmap(str(path)))
            self.img_label.setScaledContents(True)
        else:
            self.img_label.setText(self.letter)
        layout.addWidget(self.img_label)


class SignDetectiveGameView(QWidget):
    """
    Main active gameplay screen for Sign Detective:
    - Sequence of static FSL alphabet signs
    - Letter tile input boxes matching the sentence/phrase
    - Timer countdown with hourglass
    - Next button
    - Mascot checkmark celebration on correct answer
    """
    back_requested = Signal()
    close_clicked = Signal()
    game_finished = Signal(int, int)

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.resize(1920, 1080)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Background foliage
        self.bg_label = QLabel(self)
        self.bg_label.setGeometry(0, 0, 1920, 1080)
        self.bg_label.setStyleSheet("background-color: #C2D076;")

        # Header
        self.header = MinigameHeader(self)
        self.header.setGeometry(0, 0, 1920, 90)
        self.header.close_requested.connect(self.close_clicked.emit)
        self.header.raise_()

        # Main Cream Card Container
        self.card = QWidget(self)
        self.card.setGeometry(50, 95, 1820, 935)
        self.card.setStyleSheet("QWidget { background-color: #FAFFDC; border-radius: 40px; }")

        # Instruction note top-left
        self.instruction_note = QLabel("Decode the sequence of fingerspelled signs and type the sentence.", self.card)
        self.instruction_note.setGeometry(100, 40, 800, 40)
        self.instruction_note.setStyleSheet(
            "QLabel { font-family: 'Segoe UI'; font-size: 20px; font-style: italic; color: #8F8C78; background: transparent; }"
        )

        # Timer countdown top-left
        self.timer_container = QWidget(self.card)
        self.timer_container.setGeometry(90, 110, 260, 80)
        self.timer_container.setStyleSheet("background: transparent;")
        t_layout = QHBoxLayout(self.timer_container)
        t_layout.setContentsMargins(0, 0, 0, 0)
        t_layout.setSpacing(15)

        self.lbl_timer = QLabel("10s", self.timer_container)
        self.lbl_timer.setStyleSheet(
            "QLabel { font-family: 'Segoe UI'; font-size: 38px; font-weight: bold; font-style: italic; color: #704833; background: transparent; }"
        )
        t_layout.addWidget(self.lbl_timer)

        self.lbl_hourglass = QLabel(self.timer_container)
        self.lbl_hourglass.setFixedSize(50, 60)
        self.lbl_hourglass.setPixmap(QPixmap(str(ROOT / "resources/img/ui/hourglass.png")))
        self.lbl_hourglass.setScaledContents(True)
        t_layout.addWidget(self.lbl_hourglass)

        # Top-right Next Button
        self.btn_next = CircularActionButton("next", self.card)
        self.btn_next.move(1670, 70)
        self.btn_next.clicked.connect(self.next_round)

        # Signs Display Container (Upper Center)
        self.signs_container = QWidget(self.card)
        self.signs_container.setGeometry(150, 130, 1520, 340)
        self.signs_container.setStyleSheet("background: transparent;")
        self.signs_layout = QVBoxLayout(self.signs_container)
        self.signs_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Letter Tiles Input Container (Lower Center)
        self.tiles_container = QWidget(self.card)
        self.tiles_container.setGeometry(150, 500, 1520, 380)
        self.tiles_container.setStyleSheet("background: transparent;")
        self.tiles_layout = QVBoxLayout(self.tiles_container)
        self.tiles_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Mascot holding checkmark
        self.mascot_correct = QLabel(self.card)
        self.mascot_correct.setGeometry(1580, 680, 240, 240)
        self.mascot_correct.setPixmap(QPixmap(str(ROOT / "resources/img/ui/mascot_correct.png")))
        self.mascot_correct.setScaledContents(True)
        self.mascot_correct.hide()

        # Countdown timer
        self.countdown_timer = QTimer(self)
        self.countdown_timer.setInterval(100)
        self.countdown_timer.timeout.connect(self.tick)

        self.user_input = ""
        self.sign_rows = []
        self.tile_rows = []
        self.tiles_list = []

    def start_game(self):
        self.load_round()

    def load_round(self):
        self.mascot_correct.hide()
        self.btn_next.set_green(False)
        self.user_input = ""

        # Clear old rows
        for r in self.sign_rows:
            r.deleteLater()
        self.sign_rows.clear()

        for r in self.tile_rows:
            r.deleteLater()
        self.tile_rows.clear()
        self.tiles_list.clear()

        words = self.session.word.split()

        # If sentence has 4 words, group by 2 per row for balanced layout (like NICE TO / MEET YOU)
        if len(words) >= 4:
            word_groups = [words[:2], words[2:]]
        elif len(words) == 3:
            word_groups = [words[:2], words[2:]]
        elif len(words) == 2:
            word_groups = [[words[0]], [words[1]]]
        else:
            word_groups = [words]

        # 1. Build Signs Display
        for group in word_groups:
            row_w = QWidget(self.signs_container)
            row_l = QHBoxLayout(row_w)
            row_l.setSpacing(45)  # gap between words
            row_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            for w in group:
                word_w = QWidget(row_w)
                word_l = QHBoxLayout(word_w)
                word_l.setSpacing(10)
                word_l.setContentsMargins(0, 0, 0, 0)
                for ch in w:
                    if "A" <= ch.upper() <= "Z":
                        card = SignDetectiveCard(ch, word_w)
                        word_l.addWidget(card)
                row_l.addWidget(word_w)
            self.signs_layout.addWidget(row_w)
            self.sign_rows.append(row_w)

        # 2. Build Letter Tiles Input Display
        for group in word_groups:
            row_w = QWidget(self.tiles_container)
            row_l = QHBoxLayout(row_w)
            row_l.setSpacing(45)  # gap between words
            row_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            for w in group:
                word_w = QWidget(row_w)
                word_l = QHBoxLayout(word_w)
                word_l.setSpacing(12)
                word_l.setContentsMargins(0, 0, 0, 0)
                for ch in w:
                    if "A" <= ch.upper() <= "Z":
                        tile = LetterTile("", word_w)
                        word_l.addWidget(tile)
                        self.tiles_list.append((tile, ch))
                row_l.addWidget(word_w)
            self.tiles_layout.addWidget(row_w)
            self.tile_rows.append(row_w)

        self.update_tiles()
        self.countdown_timer.start()
        self.setFocus()

    def tick(self):
        secs = max(0, int(self.session.remaining))
        self.lbl_timer.setText(f"{secs}s")
        if self.session.remaining <= 0 and not self.session.resolved:
            self.resolve_round(False)

    def keyPressEvent(self, event):
        if self.session.resolved:
            super().keyPressEvent(event)
            return

        key = event.key()
        if key == Qt.Key.Key_Backspace:
            if len(self.user_input) > 0:
                self.user_input = self.user_input[:-1]
                self.update_tiles()
            return
        elif Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
            char = chr(key).upper()
            total_needed = len(self.tiles_list)
            if len(self.user_input) < total_needed:
                self.user_input += char
                self.update_tiles()

                if len(self.user_input) == total_needed:
                    self.check_answer()
            return

        super().keyPressEvent(event)

    def update_tiles(self):
        curr_len = len(self.user_input)
        for i, (tile, target_ch) in enumerate(self.tiles_list):
            if i < curr_len:
                tile.set_letter(self.user_input[i], state="filled")
            elif i == curr_len and not self.session.resolved:
                tile.set_letter("", state="active")
            else:
                tile.set_letter("", state="empty")

    def check_answer(self):
        words = self.session.word.split()
        reconstructed = []
        idx = 0
        for w in words:
            clean_w = [c for c in w if "A" <= c.upper() <= "Z"]
            length = len(clean_w)
            word_str = self.user_input[idx:idx + length]
            reconstructed.append(word_str)
            idx += length
        user_full = " ".join(reconstructed)

        if self.session.check_answer(user_full):
            self.resolve_round(True)
        else:
            for tile, _ in self.tiles_list:
                tile.set_state("wrong")
            QTimer.singleShot(600, self._reset_after_wrong)

    def _reset_after_wrong(self):
        if not self.session.resolved:
            self.user_input = ""
            self.update_tiles()

    def resolve_round(self, correct):
        if not self.session.finish(correct):
            return
        self.countdown_timer.stop()
        if correct:
            for tile, _ in self.tiles_list:
                tile.set_state("correct")
            self.btn_next.set_green(True)
            QTimer.singleShot(1200, self.next_round)
        else:
            for tile, target_ch in self.tiles_list:
                tile.set_letter(target_ch, state="revealed")
            self.btn_next.set_green(True)
            QTimer.singleShot(2200, self.next_round)

    def next_round(self):
        if not self.session.resolved:
            return
        if self.session.next_round():
            self.load_round()
        else:
            self.countdown_timer.stop()
            self.game_finished.emit(self.session.score, self.session.total)


class SignDetective(QWidget):
    """
    Complete Sign Detective experience:
    - How-To Screen (SIGNDETECTIVEHOW.png)
    - Gameplay Screen
    - Score Screen (scores_bg.png)
    """
    back_requested = Signal()
    close_clicked = Signal()

    def __init__(self, parent=None, module_code=None, *, scope=None):
        super().__init__(parent)
        self.resize(1920, 1080)
        self.scope = scope
        self.module_code = module_code
        self.session = GameSession("detective", rounds=5, module_code=module_code, scope=scope)

        self.stack = QStackedWidget(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)

        # 1. How to play
        self.how_to = HowToPlayWidget("SIGNDETECTIVEHOW.png", self)
        self.how_to.start_requested.connect(self.start_game)
        self.how_to.back_requested.connect(self.back_requested.emit)
        self.stack.addWidget(self.how_to)

        # 2. Gameplay
        self.game_view = SignDetectiveGameView(self.session, self)
        self.game_view.close_clicked.connect(self._prompt_exit)
        self.game_view.back_requested.connect(self.back_requested.emit)
        self.game_view.game_finished.connect(self.show_score)
        self.stack.addWidget(self.game_view)

        # 3. Score
        self.score_view = MinigameScoreWidget(self)
        self.score_view.continue_requested.connect(self.back_requested.emit)
        self.score_view.close_requested.connect(self.back_requested.emit)
        self.score_view.replay_requested.connect(self.start_game)
        self.stack.addWidget(self.score_view)

    def pause(self):
        self.game_view.toggle_pause()

    def play(self):
        if self.game_view.is_paused:
            self.game_view.toggle_pause()

    def replay(self):
        self.game_view.replay()

    @property
    def countdown(self):
        return self.game_view.countdown_timer

    @property
    def answer(self):
        return _AnswerProxy(self.game_view)

    def check_answer(self):
        return self.game_view.check_answer()

    def next_round(self):
        return self.game_view.next_round()

    def go_back(self):
        self.stop()
        self.back_requested.emit()

    @property
    def back_button(self):
        return getattr(self.how_to, "btn_back", None) or getattr(self.how_to, "back_button", None)

        self._fitted_form = FittedForm(self)

    def start_game(self):
        self.stack.setCurrentWidget(self.game_view)
        self.game_view.start_game()

    def show_score(self, score, total):
        self.record_score(score, total)
        self.score_view.set_score(score, total)
        self.stack.setCurrentWidget(self.score_view)

    def record_score(self, score, total):
        try:
            import uuid
            from datetime import datetime, timezone
            from backend import auth_service
            from backend.database.session import session_scope
            from backend.database.repository import upsert_minigame_attempt, rebuild_user_statistics
            from backend.leaderboard_service import notify_scores_changed

            user = auth_service.get_current_user()
            if not user:
                return
            uid = uuid.UUID(user["user_id"]) if isinstance(user["user_id"], str) else user["user_id"]

            with session_scope() as db:
                # minigame_id 6 is Sign Detective
                upsert_minigame_attempt(
                    db,
                    user_id=uid,
                    game_attempt_id=uuid.uuid4(),
                    minigame_id=6,
                    started_at=datetime.now(timezone.utc),
                    completed_at=datetime.now(timezone.utc),
                    score=score,
                    duration_seconds=60,
                    accuracy=score / max(1, total)
                )
                rebuild_user_statistics(db, uid)
            notify_scores_changed()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Failed to record minigame score: %s", e)

    def stop(self):
        self.game_view.countdown_timer.stop()

    def hideEvent(self, event):
        self.stop()
        super().hideEvent(event)

    def closeEvent(self, event):
        self.stop()
        super().closeEvent(event)

    def _prompt_exit(self):
        import os
        if hasattr(self, "game_view") and hasattr(self.game_view, "countdown_timer"):
            try:
                self.game_view.countdown_timer.stop()
            except Exception:
                pass
        if os.environ.get("QT_QPA_PLATFORM") != "offscreen":
            from screens.dialogs import WaitConfirmDialog
            dialog = WaitConfirmDialog(mode="game", parent=self)
            if dialog.exec() != WaitConfirmDialog.DialogCode.Accepted:
                if hasattr(self, "game_view") and hasattr(self.game_view, "countdown_timer"):
                    try:
                        self.game_view.countdown_timer.start()
                    except Exception:
                        pass
                return
        self.stop()
        self.back_requested.emit()
