"""
Practice-session state machines, fully decoupled from any UI toolkit.

A Qt widget hooks these up with QTimer.singleShot() in place of Tkinter's
`.after()`, and updates its own labels/progress bars from the returned
events instead of touching Tk widgets directly.
"""
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional

from . import config


class SessionState(Enum):
    WAITING  = auto()   # showing a target, waiting for a correct sign/key
    FEEDBACK = auto()   # showing "correct"/"try again", ignoring input
    DONE     = auto()   # session finished


class Event(Enum):
    NONE     = auto()
    HOLDING  = auto()   # correct sign detected, still counting toward hold_frames
    CORRECT  = auto()   # hold threshold reached / correct key pressed
    WRONG    = auto()


@dataclass
class CameraPracticeSession:
    """
    Drives a sequence of camera-recognized targets. Used for both the
    alphabet screen (pass the full alphabet, or one letter for "single"
    mode) and the word-spelling / "sign it" screen (pass a word's letters,
    or a whole shuffled queue's flattened letters — whatever list of
    single-target strings you want to step through).

    Typical Qt wiring:

        session = CameraPracticeSession(letters_of_word)

        def on_tick(self):
            result = engine.read_frame()
            ...
            if result.prediction:
                event = session.process_prediction(
                    result.prediction.label, result.prediction.confidence)
                if event is Event.CORRECT:
                    show_green_feedback(session.current_target)
                    QTimer.singleShot(1200, advance_and_refresh_ui)
                elif event is Event.WRONG:
                    show_red_feedback()
                    QTimer.singleShot(900, lambda: (session.reset_waiting(), refresh_ui()))

        def advance_and_refresh_ui(self):
            session.advance()
            if session.is_done():
                show_results_screen(session.score, session.total)
            else:
                refresh_ui()
    """
    targets: List[str]
    confidence_threshold: float = config.CONFIDENCE_THRESHOLD
    hold_frames: int = config.HOLD_FRAMES
    grace_frames: int = 4

    index: int = field(default=0, init=False)
    score: int = field(default=0, init=False)
    state: SessionState = field(default=SessionState.WAITING, init=False)
    _hold: int = field(default=0, init=False)
    _grace: int = field(default=0, init=False)
    _confidences: List[float] = field(default_factory=list, init=False)

    # ---- queries --------------------------------------------------------
    @property
    def current_target(self) -> Optional[str]:
        if self.index >= len(self.targets):
            return None
        return self.targets[self.index]

    @property
    def total(self) -> int:
        return len(self.targets)

    @property
    def hold_progress(self) -> float:
        """0.0-1.0, handy for driving a progress bar while holding a sign."""
        return min(self._hold / self.hold_frames, 1.0) if self.hold_frames else 0.0

    def is_done(self) -> bool:
        return self.state is SessionState.DONE

    def score_percent(self) -> int:
        if not self.total:
            return 0
        try:
            pct = int(round((self.score / self.total) * 100.0))
        except Exception:
            pct = 0
        return max(0, min(100, pct))

    def accuracy_percent(self) -> int:
        """Overall lesson recognition accuracy (0-100), safe against empty/NaN data."""
        if not self.total:
            return 0
        if self._confidences and len(self._confidences) == self.score and self.score > 0:
            try:
                import math
                valid = [float(c) for c in self._confidences if c is not None and math.isfinite(float(c))]
                if valid:
                    avg_conf = sum(valid) / len(valid)
                    completion_ratio = self.score / self.total
                    pct = int(round(avg_conf * 100.0 * completion_ratio))
                    return max(0, min(100, pct))
            except Exception:
                pass
        return self.score_percent()

    # ---- input ------------------------------------------------------------
    def process_prediction(self, label: str, confidence: float) -> Event:
        """Call once per camera frame while state is WAITING."""
        if self.state is not SessionState.WAITING:
            return Event.NONE
        is_match = (label == self.current_target)
        if not is_match and label is not None and self.current_target is not None:
            import re
            is_match = re.sub(r"[^A-Z0-9]", "", str(label).upper()) == re.sub(r"[^A-Z0-9]", "", str(self.current_target).upper())
        if is_match and confidence >= self.confidence_threshold:
            self._hold += 1
            self._grace = 0
            if self._hold >= self.hold_frames:
                self.score += 1
                try:
                    import math
                    val = float(confidence)
                    if math.isfinite(val):
                        self._confidences.append(max(0.0, min(1.0, val)))
                except Exception:
                    pass
                self.state = SessionState.FEEDBACK
                return Event.CORRECT
            return Event.HOLDING
        if self._hold > 0:
            if self._grace < self.grace_frames:
                self._grace += 1
                return Event.HOLDING
            self._hold = 0
            self._grace = 0
            return Event.NONE
        return Event.NONE

    # ---- transitions (call these from your QTimer.singleShot callbacks) --
    def reset_waiting(self):
        self.state = SessionState.WAITING
        self._hold = 0
        self._grace = 0

    def advance(self):
        self.index += 1
        self._hold = 0
        self._grace = 0
        self.state = SessionState.DONE if self.index >= len(self.targets) else SessionState.WAITING

    def skip(self):
        self.advance()

    def restart(self):
        self.index = 0
        self.score = 0
        self.state = SessionState.WAITING
        self._hold = 0
        self._grace = 0
        self._confidences.clear()


@dataclass
class KeyPressSpellingSession:
    """Simpler session for a keyboard-driven 'type the letter' screen."""
    word: str
    index: int = field(default=0, init=False)
    score: int = field(default=0, init=False)
    state: SessionState = field(default=SessionState.WAITING, init=False)

    def __post_init__(self):
        self.letters: List[str] = [c for c in self.word if c != ' ']

    @property
    def current_target(self) -> Optional[str]:
        if self.index >= len(self.letters):
            return None
        return self.letters[self.index]

    def is_done(self) -> bool:
        return self.state is SessionState.DONE

    def score_percent(self) -> int:
        return int(self.score / len(self.letters) * 100) if self.letters else 0

    def check_key(self, pressed_char: str) -> Event:
        """Call from your Qt key handler (e.g. keyPressEvent)."""
        if self.state is not SessionState.WAITING:
            return Event.NONE
        if pressed_char.upper() == self.current_target:
            self.score += 1
            self.state = SessionState.FEEDBACK
            return Event.CORRECT
        self.state = SessionState.FEEDBACK
        return Event.WRONG

    def reset_waiting(self):
        self.state = SessionState.WAITING

    def advance(self):
        self.index += 1
        self.state = SessionState.DONE if self.index >= len(self.letters) else SessionState.WAITING

    def restart(self):
        self.index = 0
        self.score = 0
        self.state = SessionState.WAITING
