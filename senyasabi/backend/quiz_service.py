"""One module quiz, generated from content. UAT identification needs no camera/model."""
from dataclasses import dataclass
import json
import random
from .content_service import ROOT, get_signs_for_module
from .minigame_service import normalize


@dataclass(frozen=True)
class QuizDefinition:
    quiz_code: str
    module_code: str
    title: str
    passing_score: int


def get_quiz(module_code):
    code = module_code.casefold()
    get_signs_for_module(code)  # Validate; never widen to another module.
    entries = json.loads((ROOT / "resources/data/quizzes/quizzes.json").read_text(encoding="utf-8-sig"))["quizzes"]
    item = next((item for item in entries if item["module_code"].casefold() == code), {})
    return QuizDefinition(item.get("quiz_code", f"{code}_quiz"), code,
                          item.get("title", f"{code.title()} Quiz"), item.get("passing_score", 70))


class QuizSession:
    def __init__(self, module_code, count=5):
        self.definition = get_quiz(module_code)
        pool = get_signs_for_module(module_code)
        self.questions = random.sample(pool, min(count, len(pool)))
        self.index = 0
        self.score = 0
        self.answered = False

    @property
    def complete(self):
        return self.index >= len(self.questions)

    @property
    def current(self):
        return None if self.complete else self.questions[self.index]

    def answer(self, answer):
        if self.complete or self.answered:
            return False
        correct = normalize(answer) == normalize(self.current.label)
        self.score += int(correct)
        self.answered = True
        return correct

    def advance(self):
        if self.answered:
            self.index += 1
            self.answered = False

    @property
    def percent(self):
        return round(100 * self.score / len(self.questions)) if self.questions else 0
