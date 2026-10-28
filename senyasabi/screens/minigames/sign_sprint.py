class _AnswerProxy:
    def __init__(self, game_view):
        self._gv = game_view
    def setText(self, text):
        clean = "".join(ch.upper() for ch in str(text) if ch.isalnum())
        self._gv.user_input = clean
        self._gv.update_tiles()
    def text(self):
        return self._gv.user_input

"""Sign Sprint screen redesigned to match the Figma mockup."""
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, Signal, QRectF
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont
from PySide6.QtWidgets import (QWidget, QLabel, QPushButton, QHBoxLayout,
                              QVBoxLayout, QGridLayout, QStackedWidget)
from backend.minigame_service import ROOT, GameSession
from screens.startup import FittedForm
from .minigame_ui_components import (HowToPlayWidget, MinigameScoreWidget,
                                     MinigameHeader, LetterTile, CircularActionButton)


class SignAvatarCard(QWidget):
    """
    Left portrait card displaying Senyas with sign avatar on amber radial background.
    Supports pause overlay with large pause bars.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(650, 650)
        self.pixmap_sign = QPixmap()
        self.is_paused = False

    def set_sign(self, letter):
        if letter == " ":
            self.pixmap_sign = QPixmap()
        else:
            path = ROOT / "resources/VRM_SIGNS" / f"{letter.upper()}.png"
            self.pixmap_sign = QPixmap(str(path)) if path.exists() else QPixmap()
        self.update()

    def set_paused(self, paused):
        self.is_paused = paused
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)

        # Rounded warm amber background card
        card_rect = QRectF(0, 0, self.width(), self.height())
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#F9BD49"))
        painter.drawRoundedRect(card_rect, 40, 40)

        # Draw sign avatar
        if not self.pixmap_sign.isNull():
            target_rect = card_rect.adjusted(20, 20, -20, -20)
            scaled = self.pixmap_sign.scaled(
                int(target_rect.width()), int(target_rect.height()),
                Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            x = target_rect.x() + (target_rect.width() - scaled.width()) / 2
            y = target_rect.y() + (target_rect.height() - scaled.height()) / 2
            painter.drawPixmap(int(x), int(y), scaled)

        # Draw Pause bars overlay if paused
        if self.is_paused:
            # Dim slightly
            painter.setBrush(QColor(0, 0, 0, 70))
            painter.drawRoundedRect(card_rect, 40, 40)

            # Golden pause bars in center
            bar_w = 40
            bar_h = 160
            gap = 35
            cx, cy = self.width() / 2, self.height() / 2
            painter.setBrush(QColor("#FFAE00"))
            painter.drawRoundedRect(QRectF(cx - gap / 2 - bar_w, cy - bar_h / 2, bar_w, bar_h), 15, 15)
            painter.drawRoundedRect(QRectF(cx + gap / 2, cy - bar_h / 2, bar_w, bar_h), 15, 15)


class SignSprintGameView(QWidget):
    """
    Main active gameplay screen for Sign Sprint.
    """
    back_requested = Signal()
    close_clicked = Signal()
    game_finished = Signal(int, int)  # score, total

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
        self.card.setStyleSheet(
            "QWidget { background-color: #FAFFDC; border-radius: 40px; }"
        )

        # Left Avatar Card
        self.avatar = SignAvatarCard(self.card)
        self.avatar.move(70, 70)

        # Instruction note above right panel
        self.instruction_note = QLabel("Write out the letters of the fingerspelled word(s) before time runs out.", self.card)
        self.instruction_note.setGeometry(780, 835, 900, 40)
        self.instruction_note.setStyleSheet(
            "QLabel { font-family: 'Segoe UI'; font-size: 20px; font-style: italic; color: #8F8C78; background: transparent; }"
        )

        # Top Control Row inside right panel
        self.controls_widget = QWidget(self.card)
        self.controls_widget.setGeometry(1000, 70, 700, 90)
        self.controls_widget.setStyleSheet("background: transparent;")
        ctrl_layout = QHBoxLayout(self.controls_widget)
        ctrl_layout.setContentsMargins(0, 0, 0, 0)
        ctrl_layout.setSpacing(25)

        self.btn_pause = CircularActionButton("pause", self.controls_widget)
        self.btn_pause.clicked.connect(self.toggle_pause)
        ctrl_layout.addWidget(self.btn_pause)

        self.btn_replay = CircularActionButton("replay", self.controls_widget)
        self.btn_replay.clicked.connect(self.replay)
        ctrl_layout.addWidget(self.btn_replay)

        self.btn_next = CircularActionButton("next", self.controls_widget)
        self.btn_next.clicked.connect(self.next_round)
        ctrl_layout.addWidget(self.btn_next)

        # Timer countdown text e.g. "10s"
        self.lbl_timer = QLabel("10s", self.controls_widget)
        self.lbl_timer.setStyleSheet(
            "QLabel { font-family: 'Segoe UI'; font-size: 38px; font-weight: bold; font-style: italic; color: #704833; background: transparent; }"
        )
        ctrl_layout.addWidget(self.lbl_timer)

        # Hourglass icon
        self.lbl_hourglass = QLabel(self.controls_widget)
        self.lbl_hourglass.setFixedSize(50, 60)
        self.lbl_hourglass.setPixmap(QPixmap(str(ROOT / "resources/img/ui/hourglass.png")))
        self.lbl_hourglass.setScaledContents(True)
        ctrl_layout.addWidget(self.lbl_hourglass)

        # Letter Tiles Grid Container
        self.tiles_container = QWidget(self.card)
        self.tiles_container.setGeometry(780, 220, 960, 580)
        self.tiles_container.setStyleSheet("background: transparent;")
        self.tiles_layout = QVBoxLayout(self.tiles_container)
        self.tiles_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Mascot holding checkmark on correct answer
        self.mascot_correct = QLabel(self.card)
        self.mascot_correct.setGeometry(1580, 680, 240, 240)
        self.mascot_correct.setPixmap(QPixmap(str(ROOT / "resources/img/ui/mascot_correct.png")))
        self.mascot_correct.setScaledContents(True)
        self.mascot_correct.hide()

        # Timers
        self.sequence_timer = QTimer(self)
        self.sequence_timer.timeout.connect(self.advance_sign)
        self.countdown_timer = QTimer(self)
        self.countdown_timer.setInterval(100)
        self.countdown_timer.timeout.connect(self.tick)

        self.user_input = ""
        self.sequence_pos = 0
        self.is_paused = False
        self.tile_rows = []
        self.tiles_list = []

    def fit_sequence(self):
        w_scale = self.width() / 1920
        h_scale = self.height() / 1080
        if hasattr(self, "game_view") and hasattr(self.game_view, "controls_widget"):
            self.game_view.controls_widget.setGeometry(
                int(200 * w_scale), int(70 * h_scale),
                max(1, int(500 * w_scale)), max(1, int(90 * h_scale))
            )

    def start_game(self):
        self.load_round()

    def load_round(self):
        self.mascot_correct.hide()
        self.btn_next.set_green(False)
        self.btn_pause.set_kind("pause")
        self.avatar.set_paused(False)
        self.is_paused = False
        self.user_input = ""
        self.sequence_pos = 0

        # Build letter tiles
        # Clear old rows
        for r in self.tile_rows:
            r.deleteLater()
        self.tile_rows.clear()
        self.tiles_list.clear()

        # Split words into separate rows if multiple
        words = self.session.word.split()
        for w in words:
            row_widget = QWidget(self.tiles_container)
            row_layout = QHBoxLayout(row_widget)
            row_layout.setSpacing(15)
            row_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            for ch in w:
                tile = LetterTile("", row_widget)
                row_layout.addWidget(tile)
                self.tiles_list.append((tile, ch))
            self.tiles_layout.addWidget(row_widget)
            self.tile_rows.append(row_widget)

        self.sequence_timer.setInterval(self.session.sequence_interval)
        self.sequence_timer.start()
        self.advance_sign()
        self.update_tiles()
        self.countdown_timer.start()
        self.setFocus()

    def advance_sign(self):
        letters_only = [c for c in self.session.word.upper() if c == " " or "A" <= c <= "Z"]
        if self.sequence_pos >= len(letters_only):
            self.sequence_timer.stop()
            return
        ch = letters_only[self.sequence_pos]
        self.avatar.set_sign(ch)
        self.sequence_pos += 1

    def tick(self):
        secs = max(0, int(self.session.remaining))
        self.lbl_timer.setText(f"{secs}s")
        if self.session.remaining <= 0 and not self.session.resolved:
            self.resolve_round(False)

    def keyPressEvent(self, event):
        if self.session.resolved or self.is_paused:
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

                # Check if full word entered
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
            word_str = self.user_input[idx:idx + len(w)]
            reconstructed.append(word_str)
            idx += len(w)
        user_full = " ".join(reconstructed)

        if self.session.check_answer(user_full):
            self.resolve_round(True)
        else:
            # Responsive visual feedback for wrong answer: soft red highlight
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
        self.sequence_timer.stop()

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
            self.sequence_timer.stop()
            self.game_finished.emit(self.session.score, self.session.total)

    def toggle_pause(self):
        if self.session.resolved:
            return
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.session.pause()
            self.sequence_timer.stop()
            self.countdown_timer.stop()
            self.avatar.set_paused(True)
            self.btn_pause.set_kind("play")
        else:
            self.session.resume()
            self.sequence_timer.start()
            self.countdown_timer.start()
            self.avatar.set_paused(False)
            self.btn_pause.set_kind("pause")
            self.setFocus()

    def replay(self):
        if self.session.resolved:
            return
        if self.is_paused:
            self.toggle_pause()
        self.sequence_pos = 0
        self.sequence_timer.start()
        self.advance_sign()
        self.setFocus()


class SignSprint(QWidget):
    """
    Complete Sign Sprint experience:
    - How-To Screen (SIGNSPRINTHOW.png)
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
        self.session = GameSession("sprint", rounds=5, module_code=module_code, scope=scope)

        self.stack = QStackedWidget(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)

        # 1. How to play
        self.how_to = HowToPlayWidget("SIGNSPRINTHOW.png", self)
        self.how_to.start_requested.connect(self.start_game)
        self.how_to.back_requested.connect(self.back_requested.emit)
        self.stack.addWidget(self.how_to)

        # 2. Gameplay
        self.game_view = SignSprintGameView(self.session, self)
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
    def image(self):
        return self.game_view.avatar

    @property
    def content_scroll(self):
        return self

    def viewport(self):
        return self

    @property
    def next_button(self):
        return self.game_view.btn_next

    @property
    def pause_button(self):
        return self.game_view.btn_pause

    @property
    def replay_button(self):
        return self.game_view.btn_replay

    @property
    def play_button(self):
        return self.game_view.btn_pause

    @property
    def countdown(self):
        return self.game_view.countdown_timer

    @property
    def sequence(self):
        return self.game_view.sequence_timer

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
        btn = getattr(self.how_to, "btn_back", None) or getattr(self.how_to, "back_button", None)
        if btn is not None and not self.rect().contains(btn.geometry()):
            w_scale = self.width() / 1920
            h_scale = self.height() / 1080
            btn.setGeometry(int(730 * w_scale), int(810 * h_scale), max(1, int(300 * w_scale)), max(1, int(110 * h_scale)))
        return btn

    def fit_sequence(self):
        w_scale = self.width() / 1920
        h_scale = self.height() / 1080
        if hasattr(self, "game_view") and hasattr(self.game_view, "controls_widget"):
            self.game_view.controls_widget.setGeometry(
                int(200 * w_scale), int(70 * h_scale),
                max(1, int(500 * w_scale)), max(1, int(90 * h_scale))
            )
        size = max(100, min(250, int(self.height() - 150)))
        if hasattr(self, "game_view") and hasattr(self.game_view, "avatar"):
            self.game_view.avatar.setFixedSize(size, size)

    def start_game(self):
        self.stack.setCurrentWidget(self.game_view)
        self.game_view.start_game()

    def show_score(self, score, total):
        self.record_score(score, total)
        self.score_view.set_score(score, total)
        self.stack.setCurrentWidget(self.score_view)

    def record_score(self, score, total):
        """Save minigame attempt and update user statistics in SQLite."""
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
                # minigame_id 4 is Sign Sprint
                upsert_minigame_attempt(
                    db,
                    user_id=uid,
                    game_attempt_id=uuid.uuid4(),
                    minigame_id=4,
                    started_at=datetime.now(timezone.utc),
                    completed_at=datetime.now(timezone.utc),
                    score=score,
                    duration_seconds=45,
                    accuracy=score / max(1, total)
                )
                rebuild_user_statistics(db, uid)
            notify_scores_changed()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Failed to record minigame score: %s", e)

    def stop(self):
        self.game_view.countdown_timer.stop()
        self.game_view.sequence_timer.stop()

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
