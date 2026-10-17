"""Local minigame content and timed round state; no Qt, camera, or database."""
import json
import random
import re
from pathlib import Path
from time import monotonic

ROOT = Path(__file__).resolve().parents[1]
CONFIG = {
    "sprint": ("Sign Sprint", "Easy / Timed", 45),
    "quest": ("FingerSpell Quest", "Intermediate / Timed", 75),
    "detective": ("Sign Detective", "Advanced / Timed", 60),
}


def letters(label):
    return [char for char in label.upper() if "A" <= char <= "Z"]


def load_vocabulary(module_code=None):
    if module_code is not None and module_code.casefold() == "alphabet":
        return list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    entries = json.loads((ROOT / "resources/data/105labels.json").read_text(encoding="utf-8-sig"))
    if module_code is not None:
        entries = [entry for entry in entries
                   if entry["category"].casefold() == module_code.casefold()]
        if not entries:
            raise ValueError(f"Unknown module: {module_code}")
    # Exclude damaged/non-alphabetic labels, retaining original words and punctuation.
    return [entry["label"].strip() for entry in entries
            if re.fullmatch(r"[A-Z]+(?:[ '’]+[A-Z]+)*", entry["label"].strip())]


def get_words_for_module(module_code):
    """One source for module-scoped game vocabulary; never fall back to other modules."""
    return load_vocabulary(module_code)


def normalize(answer):
    return " ".join(answer.upper().replace("’", "'").split())


class GameSession:
    def __init__(self, kind, rounds=5, clock=monotonic, module_code=None):
        self.kind, self.total, self.clock = kind, rounds, clock
        self.limit = CONFIG[kind][2]
        self.module_code = module_code
        pool = get_words_for_module(module_code)
        if kind in ("sprint", "quest"):
            pool = [word for word in pool if len(letters(word)) <= (12 if kind == "sprint" else 14)]
        if not pool:
            raise ValueError(f"No playable content for module: {module_code}")
        self.words = random.sample(pool, min(rounds, len(pool)))
        self.total = len(self.words)
        self.index = -1
        self.score = 0
        self.deadline = None
        self.saved_time = None
        self.resolved = True
        self.next_round()

    @property
    def word(self):
        return self.words[self.index] if not self.complete else ""

    @property
    def complete(self):
        return self.index >= self.total

    @property
    def remaining(self):
        if self.saved_time is not None:
            return self.saved_time
        return max(0, (self.deadline or self.clock()) - self.clock())

    @property
    def sequence_interval(self):
        return max(220, 850 - self.index * 120)

    def next_round(self):
        if not self.resolved or self.complete:
            return False
        self.index += 1
        self.resolved = self.complete
        self.saved_time = None
        self.deadline = self.clock() + self.limit
        return not self.complete

    def pause(self):
        if self.saved_time is None and not self.resolved:
            self.saved_time = self.remaining

    def resume(self):
        if self.saved_time is not None:
            self.deadline = self.clock() + self.saved_time
            self.saved_time = None

    def finish(self, correct=False):
        if self.resolved:
            return False
        self.resolved = True
        self.score += int(correct and self.remaining > 0)
        return True

    def check_answer(self, answer):
        return normalize(answer) == normalize(self.word)
