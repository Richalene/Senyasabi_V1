"""Local minigame content and timed round state; no Qt, camera, or database."""
import random
from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from .content_service import MODULE_CODES, fingerspell_text, get_words_for_module as module_words

ROOT = Path(__file__).resolve().parents[1]
CONFIG = {
    "sprint": ("Sign Sprint", "Easy / Timed", 45),
    "quest": ("FingerSpell Quest", "Intermediate / Timed", 75),
    "detective": ("Sign Detective", "Advanced / Timed", 60),
}


@dataclass(frozen=True)
class MinigameContext:
    """The entry route owns game content and the Back destination."""
    scope: str = "global"
    module_code: str | None = None

    def __post_init__(self):
        if self.scope not in ("global", "module"):
            raise ValueError(f"Unknown minigame scope: {self.scope}")
        if self.scope == "global" and self.module_code is not None:
            raise ValueError("Global minigames cannot have a module.")
        if self.scope == "module" and not self.module_code:
            raise ValueError("Module minigames require a module.")
        if self.module_code is not None:
            object.__setattr__(self, "module_code", self.module_code.casefold())


def letters(label):
    return [char for char in label.upper() if "A" <= char <= "Z"]


def playable_words(labels):
    """Labels -> unique fingerspellable words ('100' -> 'ONE HUNDRED')."""
    seen, words = set(), []
    for label in labels:
        word = fingerspell_text(label)
        if word and word not in seen:
            seen.add(word)
            words.append(word)
    return words


def load_vocabulary(module_code=None):
    if module_code is not None:
        return get_words_for_module(module_code)
    return get_all_minigame_words()


def get_all_minigame_words():
    """Labels from every word module; Alphabet has its own scoped activities."""
    return [word for code in MODULE_CODES for word in module_words(code)]


def get_words_for_module(module_code):
    """One source for module-scoped game vocabulary; never fall back to other modules."""
    return module_words(module_code)


def normalize(answer):
    return " ".join(answer.upper().replace("’", "'").split())


class GameSession:
    def __init__(self, kind, rounds=5, clock=monotonic, module_code=None, *, scope=None):
        self.kind, self.total, self.clock = kind, rounds, clock
        self.limit = CONFIG[kind][2]
        # Direct callers may supply just a module; navigation always supplies scope.
        self.context = MinigameContext(
            scope if scope is not None else ("module" if module_code is not None else "global"),
            module_code)
        self.scope, self.module_code = self.context.scope, self.context.module_code
        labels = (get_all_minigame_words() if self.scope == "global"
                  else get_words_for_module(self.module_code))
        pool = playable_words(labels)
        if kind in ("sprint", "quest"):
            pool = [word for word in pool if len(letters(word)) <= (12 if kind == "sprint" else 14)]
        if not pool:
            raise ValueError(f"No playable content for {self.scope} minigames: {self.module_code}")
        self.pool = pool
        self.words = random.sample(self.pool, min(rounds, len(self.pool)))
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