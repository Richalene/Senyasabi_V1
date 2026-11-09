"""Two-section quiz generation from the local SQLite cache. No Qt, no camera."""
from dataclasses import dataclass
import random

from sqlalchemy import func, select

from .database import models as m
from .recognition_labels import normalize_label

WRONG_CHOICES = 3  # 4 options per multiple-choice question


@dataclass(frozen=True)
class SignInfo:
    sign_id: int
    sign_code: str
    label: str
    recognition_label: str


@dataclass(frozen=True)
class Question:
    kind: str                 # "multiple_choice" | "camera"
    sign: SignInfo
    prompt: str
    choices: tuple = ()       # MC only
    answer: str = ""          # MC: label; camera: recognition_label


@dataclass(frozen=True)
class QuizPlan:
    quiz_id: int
    quiz_code: str
    title: str
    passing_score: int
    time_limit_seconds: int | None
    module_code: str
    questions: list


def _info(sign):
    return SignInfo(sign.sign_id, sign.sign_code, sign.label, sign.recognition_label)


def _load_module(db, module_code):
    module = db.scalar(select(m.Module).where(
        func.lower(m.Module.module_code) == module_code.casefold(),
        m.Module.is_deleted.is_(False), m.Module.is_active.is_(True)))
    if module is None:
        raise ValueError(f"Unknown module: {module_code}")
    return module


def _load_quiz(db, module, category_code):
    cat = (m.Quiz.category_code.is_(None) if category_code is None
           else m.Quiz.category_code == category_code)
    quiz = db.scalar(select(m.Quiz).where(
        m.Quiz.module_id == module.module_id, m.Quiz.is_deleted.is_(False), cat))
    if quiz is None:
        raise ValueError(f"No quiz for {module.module_code}/{category_code}")
    return quiz


def module_signs(db, module_id):
    """All signs in a module, lesson order then display order (distractor pool)."""
    lesson_order = func.min(m.Lesson.lesson_order)
    display_order = func.min(m.LessonSign.display_order)
    rows = db.execute(
        select(m.Sign)
        .join(m.LessonSign, m.LessonSign.sign_id == m.Sign.sign_id)
        .join(m.Lesson, m.Lesson.lesson_id == m.LessonSign.lesson_id)
        .where(m.Lesson.parent_module == module_id,
               m.Lesson.is_active.is_(True), m.Lesson.is_deleted.is_(False),
               m.LessonSign.is_deleted.is_(False), m.Sign.is_deleted.is_(False))
        .group_by(m.Sign.sign_id)
        .order_by(lesson_order, display_order)).scalars().all()
    return [_info(s) for s in rows]


def quiz_signs(db, quiz_id):
    rows = db.execute(
        select(m.Sign)
        .join(m.QuizSign, m.QuizSign.sign_id == m.Sign.sign_id)
        .where(m.QuizSign.quiz_id == quiz_id, m.QuizSign.is_deleted.is_(False),
               m.Sign.is_deleted.is_(False))
        .order_by(m.QuizSign.display_order)).scalars().all()
    return [_info(s) for s in rows]


def build_questions(signs, pool, config=None, *, max_signs=None, include_camera=True, rng=random):
    """MC section first, then camera. Each sign yields one question per section."""
    config = config or {}
    types = set(config.get("question_types") or ("camera", "identification"))
    want_mc = bool(types & {"identification", "multiple_choice"})
    want_camera = include_camera and "camera" in types

    chosen = list(signs)
    if config.get("shuffle", True):
        rng.shuffle(chosen)
    if max_signs:
        chosen = chosen[:max_signs]

    multiple_choice, camera = [], []
    for sign in chosen:
        if want_mc:
            seen = {sign.label.casefold()}
            others = []
            for p in pool:
                if p.label.casefold() not in seen:
                    seen.add(p.label.casefold())
                    others.append(p)
            wrong = rng.sample(others, min(WRONG_CHOICES, len(others)))
            choices = [sign.label] + [w.label for w in wrong]
            rng.shuffle(choices)
            multiple_choice.append(Question("multiple_choice", sign, "What does this sign mean?",
                                            tuple(choices), sign.label))
        if want_camera:
            camera.append(Question("camera", sign, f"Perform the sign for {sign.label}",
                                   (), sign.recognition_label))
    return multiple_choice + camera


def generate_quiz(module_code, category_code=None, *, max_signs=None, include_camera=True, rng=random):
    from .database.session import session_scope
    with session_scope() as db:
        module = _load_module(db, module_code)
        quiz = _load_quiz(db, module, category_code)
        pool = module_signs(db, module.module_id)
        signs = quiz_signs(db, quiz.quiz_id) or pool   # fall back to the whole module
        if not signs:
            raise ValueError(f"No signs for {module_code}")
        questions = build_questions(signs, pool, quiz.config, max_signs=max_signs,
                                    include_camera=include_camera, rng=rng)
        return QuizPlan(quiz.quiz_id, quiz.quiz_code, quiz.title, quiz.passing_score,
                        quiz.time_limit_seconds, module.module_code, questions)


def check_answer(question, given):
    """MC: the chosen label. Camera: the model's predicted label."""
    if question.kind == "camera":
        return normalize_label(given) == normalize_label(question.answer)
    return given.strip().casefold() == question.answer.casefold()


def summarize(plan, correct_flags):
    """correct_flags is aligned with plan.questions. Returns queue_quiz_attempt kwargs."""
    def acc(kind):
        flags = [ok for q, ok in zip(plan.questions, correct_flags) if q.kind == kind]
        return round(100 * sum(flags) / len(flags), 2) if flags else None
    total, score = len(plan.questions), sum(correct_flags)
    pct = round(100 * score / total, 2) if total else 0.0
    return dict(quiz_id=plan.quiz_id, score=score, max_score=total, percentage=pct,
                passed=pct >= plan.passing_score,
                camera_accuracy=acc("camera"), mc_accuracy=acc("multiple_choice"))