from datetime import datetime, timezone, date
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session
import uuid
import json
from typing import Any, Literal

from .models import (
    User,
    ContentVersion,
    MediaFile,
    MediaCache,
    Module,
    Lesson,
    Sign,
    Quiz,
    Minigame,
    MinigameSign,
    Badge,
    UserBadges,
    LessonProgress,
    UserStatistics,
    Streak,
    LeaderboardCache,
    QuizAttempt,
    MinigameAttempt,
    OfflineAuth,
    SyncQueue,
    LessonSign,
    SignMedia,
    QuizSign,    
)

def normalize_email(email: str) -> str:
    return email.strip().lower()

# ══════════════════════════════════════════════════════════════════════
# users
# ══════════════════════════════════════════════════════════════════════

def upsert_user(
    db: Session,
    user_id: uuid.UUID,
    username: str,
    email: str | None = None,
    display_name: str | None = None,
) -> User:
    """Mirror a server profile locally. Flushes only; the caller owns the transaction."""
    username = username.strip()
    if not username:
        raise ValueError("Username is required")
    email = normalize_email(email) if email else None

    user = db.get(User, user_id)
    if user is None:
        user = User(user_id=user_id, username=username, email=email, display_name=display_name)
        db.add(user)
    else:
        user.username = username
        user.email = email
        user.display_name = display_name
    db.flush()
    return user

def get_user_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    return db.get(User, user_id)

def get_user_by_username(db: Session, username: str) -> User | None:
    statement = select(User).where(func.lower(User.username) == username.strip().lower())
    return db.scalar(statement)

def update_user_profile(
    db: Session,
    user_id: uuid.UUID,
    display_name: str | None = None,
) -> User | None:
    user = db.get(User, user_id)

    if user is None:
        return None

    if display_name is not None:
        user.display_name = display_name
    user.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(user)

    return user


def delete_user(db: Session, user_id: uuid.UUID) -> bool:
    user = db.get(User, user_id)

    if user is None:
        return False

    db.delete(user)
    db.commit()

    return True

# ══════════════════════════════════════════════════════════════════════
# content_versions
# ══════════════════════════════════════════════════════════════════════

def create_content_version(
    db: Session,
    version_number: int,
    changelog: str | None = None,
    is_published: bool = False,
) -> ContentVersion:
    if changelog is not None:
        changelog = changelog.strip()

    content_version = ContentVersion(
        version_number=version_number,
        changelog=changelog,
        is_published=is_published,
    )

    db.add(content_version)
    db.commit()
    db.refresh(content_version)

    return content_version


def get_content_version(
    db: Session,
    content_version_id: int,
) -> ContentVersion | None:
    return db.get(ContentVersion, content_version_id)


def get_content_version_by_number(
    db: Session,
    content_version_id: int,
) -> ContentVersion | None:
    statement = select(ContentVersion).where(ContentVersion.version_number == content_version_id)
    return db.scalar(statement)


def update_content_version(
    db: Session,
    content_version_id: int,
    **fields,
) -> ContentVersion | None:
    content_version = db.get(ContentVersion, content_version_id)

    if content_version is None:
        return None

    allowed_fields = {
        "version_number",
        "changelog",
        "is_published",
    }

    for key, value in fields.items():
        if key not in allowed_fields:
            raise ValueError(f"Cannot update field: {key}")

        if key == "changelog" and value is not None:
            value = value.strip()

        setattr(content_version, key, value)

    db.commit()
    db.refresh(content_version)

    return content_version

def delete_content_version(
    db: Session,
    content_version_id: int,
) -> bool:
    content_version = db.get(ContentVersion, content_version_id)

    if content_version is None:
        return False

    content_version.is_deleted = True
    db.commit()

    return True

# ══════════════════════════════════════════════════════════════════════
# media_files
# ══════════════════════════════════════════════════════════════════════

def create_media_file(
    db: Session,
    media_id: int,
    file_name: str,
    object_key: str,
    media_type: str,
    content_version_id: int,
    file_size: int | None = None,
    checksum: str | None = None,
) -> MediaFile:
    file_name = file_name.strip()
    object_key = object_key.strip()
    media_type = media_type.strip()

    if not file_name:
        raise ValueError("File name is required")
    if not object_key:
        raise ValueError("Object key is required")
    if media_type not in ("Image", "Video"):
        raise ValueError("media_type must be 'Image' or 'Video'")

    media_file = MediaFile(
        media_id=media_id,
        file_name=file_name,
        object_key=object_key,
        media_type=media_type,
        content_version_id=content_version_id,
        file_size=file_size,
        checksum=checksum,
    )

    media_file = db.merge(media_file)
    db.commit()
    db.refresh(media_file)

    return media_file


def get_media_file(
    db: Session,
    media_id: int,
) -> MediaFile | None:
    return db.get(MediaFile, media_id)


def update_media_file(
    db: Session,
    media_id: int,
    **fields,
) -> MediaFile | None:
    media_file = db.get(MediaFile, media_id)

    if media_file is None:
        return None

    allowed_fields = {
        "file_name",
        "object_key",
        "media_type",
        "file_size",
        "content_version",
    }

    for key, value in fields.items():
        if key not in allowed_fields:
            raise ValueError(f"Cannot update field: {key}")
        if key == "media_type" and value not in ("Image", "Video"):
            raise ValueError("media_type must be 'Image' or 'Video'")
        setattr(media_file, key, value)

    db.commit()
    db.refresh(media_file)

    return media_file


def delete_media_file(
    db: Session,
    media_id: int,
) -> bool:
    media_file = db.get(MediaFile, media_id)

    if media_file is None:
        return False

    media_file.is_deleted = True
    db.commit()

    return True

# ══════════════════════════════════════════════════════════════════════
# media_cache
# ══════════════════════════════════════════════════════════════════════

def create_media_cache(
    db: Session,
    media_id: int,
    local_path: str | None,
    content_version_id: int,
    checksum: str | None = None,
) -> MediaCache:
    media_cache = MediaCache(
        media_id=media_id,
        local_path=local_path,
        content_version_id=content_version_id,
        checksum=checksum,
    )

    db.add(media_cache)
    db.commit()
    db.refresh(media_cache)

    return media_cache


def get_media_cache(
    db: Session,
    media_id: int,
) -> MediaCache | None:
    return db.get(MediaCache, media_id)


def delete_media_cache(
    db: Session,
    media_id: int,
) -> bool:
    media_cache = db.get(MediaCache, media_id)
    if media_cache is None:
        return False

    db.delete(media_cache)
    db.commit()
    return True

# ══════════════════════════════════════════════════════════════════════
# modules
# ══════════════════════════════════════════════════════════════════════

def create_module(
    db: Session,
    module_id: int,
    module_code: str,
    title: str,
    content_version_id: int,
    module_order: int,
    description: str | None = None,
) -> Module:
    module_code = module_code.strip()
    title = title.strip()

    if not module_code:
        raise ValueError("Module code cannot be empty")
    if not title:
        raise ValueError("Title cannot be empty")
    if not module_order:
        raise ValueError("Module order cannot be empty")
    if not content_version_id:
        raise ValueError("Content version cannot be empty")
    if description is not None:
        description = description.strip()

    module = Module(
        module_id=module_id,
        module_code=module_code,
        title=title,
        description=description,
        module_order=module_order,
        content_version_id=content_version_id,
    )

    module = db.merge(module)
    db.commit()
    db.refresh(module)

    return module


def get_module(
    db: Session,
    module_id: int,
) -> Module | None:
    return db.get(Module, module_id)


def list_modules(
    db: Session,
    active_only: bool = True,
) -> list[Module]:
    query = db.query(Module).filter(Module.is_deleted == False)

    if active_only:
        query = query.filter(Module.is_active == True)

    return query.order_by(Module.module_order).all()


def update_module(
    db: Session,
    module_id: int,
    **fields,
) -> Module | None:
    module = db.get(Module, module_id)

    if module is None:
        return None

    allowed_fields = {
        "module_code",
        "title",
        "description",
        "module_order",
        "is_active",
        "content_version",
    }

    for key, value in fields.items():
        if key not in allowed_fields:
            raise ValueError(f"Cannot update field: {key}")

        if key == "title":
            value = value.strip()
            if not value:
                raise ValueError("title cannot be empty")

        if key == "description" and value is not None:
            value = value.strip()

        setattr(module, key, value)

    db.commit()
    db.refresh(module)

    return module


def deactivate_module(
    db: Session,
    module_id: int,
) -> Module | None:
    module = db.get(Module, module_id)

    if module is None:
        return None

    module.is_active = False
    db.commit()
    db.refresh(module)

    return module


def delete_module(
    db: Session,
    module_id: int,
) -> bool:
    module = db.get(Module, module_id)

    if module is None:
        return False

    module.is_deleted = True
    db.commit()

    return True

# ══════════════════════════════════════════════════════════════════════
# lessons
# ══════════════════════════════════════════════════════════════════════

def create_lesson(
    db: Session,
    lesson_id: int,
    lesson_code: str,
    title: str,
    content_version_id: int,
    parent_module: int,
    lesson_order: int,
    description: str | None = None,
) -> Lesson:
    lesson_code = lesson_code.strip()
    title = title.strip()

    if not lesson_code:
        raise ValueError("Lesson code cannot be empty")
    if not title:
        raise ValueError("title cannot be empty")
    if not parent_module:
        raise ValueError("parent_module cannot be empty")
    if not content_version_id:
        raise ValueError("content_version cannot be empty")
    if not lesson_order:
        raise ValueError("lesson_order cannot be empty")
    if description is not None:
        description = description.strip()

    lesson = Lesson(
        lesson_id=lesson_id,
        lesson_code=lesson_code,
        title=title,
        description=description,
        parent_module=parent_module,
        lesson_order=lesson_order,
        content_version_id=content_version_id,
    )

    lesson = db.merge(lesson)
    db.commit()
    db.refresh(lesson)

    return lesson


def get_lesson(
    db: Session,
    lesson_id: int,
) -> Lesson | None:
    return db.get(Lesson, lesson_id)


def list_lessons(
    db: Session,
    active_only: bool = True,
) -> list[Lesson]:
    query = db.query(Lesson).filter(Lesson.is_deleted == False)

    if active_only:
        query = query.filter(Lesson.is_active == True)

    return query.order_by(Lesson.lesson_order).all()


def update_lesson(
    db: Session,
    lesson_id: int,
    **fields,
) -> Lesson | None:
    lesson = db.get(Lesson, lesson_id)

    if lesson is None:
        return None

    allowed_fields = {
        "lesson_code",
        "title",
        "description",
        "lesson_order",
        "parent_module",
        "is_active",
        "content_version",
    }

    for key, value in fields.items():
        if key not in allowed_fields:
            raise ValueError(f"Cannot update field: {key}")
        if key == "title":
            value = value.strip()
            if not value:
                raise ValueError("Title cannot be empty")
        if key == "description" and value is not None:
            value = value.strip()

        setattr(lesson, key, value)

    db.commit()
    db.refresh(lesson)

    return lesson


def deactivate_lesson(
    db: Session,
    lesson_id: int,
) -> Lesson | None:
    lesson = db.get(Lesson, lesson_id)

    if lesson is None:
        return None

    lesson.is_active = False
    db.commit()
    db.refresh(lesson)

    return lesson


def delete_lesson(
    db: Session,
    lesson_id: int,
) -> bool:
    lesson = db.get(Lesson, lesson_id)

    if lesson is None:
        return False

    lesson.is_deleted = True
    db.commit()

    return True

# ══════════════════════════════════════════════════════════════════════
# signs
# ══════════════════════════════════════════════════════════════════════

def create_sign(
    db: Session,
    sign_id: int,
    sign_code: str,
    label: str,
    recognition_label: str,
    content_version_id: int,
) -> Sign:
    sign_code, label, recognition_label = (
        sign_code.strip(), label.strip(), recognition_label.strip())
    if not sign_code:
        raise ValueError("Sign code cannot be empty")
    if not label:
        raise ValueError("Label cannot be empty")
    if not recognition_label:
        raise ValueError("Recognition label cannot be empty")

    sign = Sign(
        sign_id=sign_id, sign_code=sign_code, label=label,
        recognition_label=recognition_label, content_version_id=content_version_id,
    )
    sign = db.merge(sign)
    db.commit()
    db.refresh(sign)
    return sign

def link_sign_to_lesson(db: Session, lesson_id: int, sign_id: int,
                        content_version_id: int, display_order: int = 1) -> LessonSign:
    link = db.merge(LessonSign(
        lesson_id=lesson_id, sign_id=sign_id, display_order=display_order,
        is_deleted=False, content_version_id=content_version_id))
    db.commit()
    return link


def link_sign_media(db: Session, sign_id: int, media_id: int, content_version_id: int,
                    media_role: str = "demonstration", display_order: int = 1) -> SignMedia:
    link = db.merge(SignMedia(
        sign_id=sign_id, media_id=media_id, media_role=media_role,
        display_order=display_order, is_deleted=False,
        content_version_id=content_version_id))
    db.commit()
    return link


def link_quiz_sign(db: Session, quiz_id: int, sign_id: int,
                   content_version_id: int, display_order: int = 1) -> QuizSign:
    link = db.merge(QuizSign(
        quiz_id=quiz_id, sign_id=sign_id, display_order=display_order,
        is_deleted=False, content_version_id=content_version_id))
    db.commit()
    return link

def get_sign(
    db: Session,
    sign_id: int,
) -> Sign | None:
    return db.get(Sign, sign_id)


def list_signs(db: Session, lesson_id: int | None = None) -> list[Sign]:
    query = select(Sign).where(Sign.is_deleted.is_(False))
    if lesson_id is not None:
        query = (
            query.join(LessonSign, LessonSign.sign_id == Sign.sign_id)
            .where(LessonSign.lesson_id == lesson_id, LessonSign.is_deleted.is_(False))
            .order_by(LessonSign.display_order)
        )
    return list(db.scalars(query))


def update_sign(
    db: Session,
    sign_id: int,
    **fields,
) -> Sign | None:
    sign = db.get(Sign, sign_id)

    if sign is None:
        return None

    allowed_fields = {
        "sign_code",
        "label",
        "recognition_label",
        "content_version_id",
    }

    for key, value in fields.items():
        if key not in allowed_fields:
            raise ValueError(f"Cannot update field: {key}")

        if key == "label":
            value = value.strip()
            if not value:
                raise ValueError("Label cannot be empty")

        if key == "recognition_label":
            value = value.strip()
            if not value:
                raise ValueError("Recognition label cannot be empty")

        setattr(sign, key, value)

    db.commit()
    db.refresh(sign)

    return sign


def delete_sign(
    db: Session,
    sign_id: int,
) -> bool:
    sign = db.get(Sign, sign_id)

    if sign is None:
        return False

    sign.is_deleted = True
    db.commit()

    return True

# ══════════════════════════════════════════════════════════════════════
# quizzes
# ══════════════════════════════════════════════════════════════════════

def create_quiz(
    db: Session,
    quiz_id: int,
    quiz_code: str,
    module_id: int,
    content_version_id: int,
    title: str,
    category_code: str | None = None,
    passing_score: int = 70,
    time_limit_seconds: int | None = None,
    config: dict | None = None,
) -> Quiz:
    quiz_code, title = quiz_code.strip(), title.strip()

    if not quiz_code or not title:
        raise ValueError("quiz_code and title are required")
    if not (0 <= passing_score <= 100):
        raise ValueError("passing_score must be between 0 and 100")
    if time_limit_seconds is not None and time_limit_seconds <= 0:
        raise ValueError("time_limit_seconds must be positive")

    quiz = Quiz(
        quiz_id=quiz_id, quiz_code=quiz_code, category_code=category_code,
        config=config or {},
        module_id=module_id,
        title=title,
        passing_score=passing_score,
        time_limit_seconds=time_limit_seconds,
        content_version_id=content_version_id,
    )

    quiz = db.merge(quiz)
    db.commit()
    db.refresh(quiz)

    return quiz


def get_quiz(
    db: Session,
    quiz_id: int,
) -> Quiz | None:
    return db.get(Quiz, quiz_id)


def update_quiz(
    db: Session,
    quiz_id: int,
    **fields,
) -> Quiz | None:
    quiz = db.get(Quiz, quiz_id)

    if quiz is None:
        return None

    allowed_fields = {
        "module_id",
        "title",
        "passing_score",
        "time_limit_seconds",
        "content_version",
    }

    for key, value in fields.items():
        if key not in allowed_fields:
            raise ValueError(f"Cannot update field: {key}")
        if key == "title" and value is not None:
            value = value.strip()
            if not value:
                value = None
        if key == "passing_score" and value is not None and not (0 <= value <= 100):
            raise ValueError("passing_score must be between 0 and 100")
        if key == "time_limit_seconds" and value is not None and value <= 0:
            raise ValueError("time_limit_seconds must be positive")

        setattr(quiz, key, value)

    db.commit()
    db.refresh(quiz)

    return quiz


def delete_quiz(
    db: Session,
    quiz_id: int,
) -> bool:
    quiz = db.get(Quiz, quiz_id)

    if quiz is None:
        return False

    quiz.is_deleted = True
    db.commit()

    return True

# ══════════════════════════════════════════════════════════════════════
# minigames
# ══════════════════════════════════════════════════════════════════════

def create_minigame(
    db: Session,
    minigame_id: int,
    minigame_code: str,
    module_id: int,
    content_version_id: int,
    game_name: str,
    game_type: str,
    description: str | None = None,
    config: dict | None = None,
) -> Minigame:
    minigame_code = minigame_code.strip()

    if not minigame_code:
        raise ValueError("Minigame code cannot be empty")
    if description is not None:
        description = description.strip()
        if not description:
            description = None
    game_name = game_name.strip()
    game_type = game_type.strip()

    minigame = Minigame(
        minigame_id=minigame_id,
        module_id=module_id,
        game_name=game_name,
        game_type=game_type,
        description=description,
        minigame_code=minigame_code.strip(), 
        content_version_id=content_version_id,
        config=config or {},
    )

    minigame = db.merge(minigame)
    db.commit()
    db.refresh(minigame)

    return minigame


def get_minigame(
    db: Session,
    minigame_id: int,
) -> Minigame | None:
    return db.get(Minigame, minigame_id)


def list_minigames(
    db: Session,
    module_id: int | None = None,
    game_type: str | None = None,
) -> list[Minigame]:
    query = db.query(Minigame).filter(Minigame.is_deleted == False)

    if module_id is not None:
        query = query.filter(Minigame.module_id == module_id)
    if game_type is not None:
        query = query.filter(Minigame.game_type == game_type)
    return query.all()


def update_minigame(
    db: Session,
    minigame_id: int,
    **fields,
) -> Minigame | None:
    minigame = db.get(Minigame, minigame_id)

    if minigame is None:
        return None

    allowed_fields = {
        "module_id",
        "game_name",
        "game_type",
        "description",
        "config",
        "content_version",
    }

    for key, value in fields.items():
        if key not in allowed_fields:
            raise ValueError(f"Cannot update field: {key}")
        if key in ("game_name", "game_type", "description") and value is not None:
            value = value.strip()
            if not value:
                value = None
        setattr(minigame, key, value)

    db.commit()
    db.refresh(minigame)

    return minigame


def delete_minigame(
    db: Session,
    minigame_id: int,
) -> bool:
    minigame = db.get(Minigame, minigame_id)

    if minigame is None:
        return False

    minigame.is_deleted = True
    db.commit()

    return True

# ══════════════════════════════════════════════════════════════════════
# minigame_signs
# ════════════════════════════════════════════════════════════════════

def add_minigame_sign(
    db: Session,
    minigame_id: int,
    sign_id: int,
) -> MinigameSign:
    minigame_sign = MinigameSign(
        minigame_id=minigame_id,
        sign_id=sign_id,
    )
    db.add(minigame_sign)
    db.commit()
    db.refresh(minigame_sign)
    return minigame_sign


def remove_minigame_sign(
    db: Session,
    minigame_id: int,
    sign_id: int,
) -> bool:
    minigame_sign = db.get(MinigameSign, (minigame_id, sign_id))
    if minigame_sign is None:
        return False

    db.delete(minigame_sign)
    db.commit()
    return True


def list_minigame_signs(
    db: Session,
    minigame_id: int,
) -> list[MinigameSign]:
    statement = select(MinigameSign).where(MinigameSign.minigame_id == minigame_id)
    return list(db.scalars(statement))

# ══════════════════════════════════════════════════════════════════════
# badge
# ══════════════════════════════════════════════════════════════════════

def create_badge(
    db: Session,
    badge_id: int,
    badge_code: str,
    badge_name: str,
    description: str | None = None,
) -> Badge:
    badge_name = badge_name.strip()

    if not badge_name:
        raise ValueError("Badge name cannot be empty")

    if description is not None:
        description = description.strip()
        if not description:
            description = None

    badge = Badge(
        badge_id=badge_id,
        badge_code=badge_code.strip(),
        badge_name=badge_name,
        description=description,
    )

    badge = db.merge(badge)
    db.commit()
    db.refresh(badge)

    return badge


def get_badge(
    db: Session,
    badge_id: int,
) -> Badge | None:
    return db.get(Badge, badge_id)


def list_badges(
    db: Session,
) -> list[Badge]:
    return db.query(Badge).all()


def update_badge(
    db: Session,
    badge_id: int,
    **fields,
) -> Badge | None:
    badge = db.get(Badge, badge_id)

    if badge is None:
        return None

    allowed_fields = {
        "badge_name",
        "description",
    }

    for key, value in fields.items():
        if key not in allowed_fields:
            raise ValueError(f"Cannot update field: {key}")

        if key == "badge_name":
            value = value.strip()
            if not value:
                raise ValueError("Badge name cannot be empty")

        if key == "description" and value is not None:
            value = value.strip()
            if not value:
                value = None

        setattr(badge, key, value)

    db.commit()
    db.refresh(badge)

    return badge


def delete_badge(
    db: Session,
    badge_id: int,
) -> bool:
    badge = db.get(Badge, badge_id)

    if badge is None:
        return False

    badge.is_deleted = True
    db.commit()

    return True

# ══════════════════════════════════════════════════════════════════════
# user_badges
# ══════════════════════════════════════════════════════════════════════

def award_badge(
    db: Session,
    user_id: uuid.UUID,
    badge_id: int,
) -> UserBadges:
    existing = db.get(UserBadges, (user_id, badge_id))
    if existing is not None:
        raise ValueError(f"User {user_id} already has badge {badge_id}")

    user_badge = UserBadges(
        user_id=user_id,
        badge_id=badge_id,
    )

    db.add(user_badge)
    db.commit()
    db.refresh(user_badge)

    return user_badge


def get_user_badge(
    db: Session,
    user_id: uuid.UUID,
    badge_id: int,
) -> UserBadges | None:
    return db.get(UserBadges, (user_id, badge_id))


def list_user_badges(
    db: Session,
    user_id: uuid.UUID,
) -> list[UserBadges]:
    return (
        db.query(UserBadges)
        .filter(UserBadges.user_id == user_id)
        .all()
    )


def revoke_badge(
    db: Session,
    user_id: uuid.UUID,
    badge_id: int,
) -> bool:
    user_badge = db.get(UserBadges, (user_id, badge_id))

    if user_badge is None:
        return False

    db.delete(user_badge)
    db.commit()

    return True

# ══════════════════════════════════════════════════════════════════════
# lesson_progress
# ══════════════════════════════════════════════════════════════════════

def get_lesson_progress(
    db: Session,
    user_id: uuid.UUID,
    lesson_id: int,
) -> LessonProgress | None:
    return db.get(LessonProgress, (user_id, lesson_id))


def create_or_update_lesson_progress(
    db: Session,
    user_id: uuid.UUID,
    lesson_id: int,
    completion_percentage: float = 0.0,
    status: str = "Not Started",
    last_accessed: datetime | None = None,
    completed_at: datetime | None = None,
    time_spent_seconds: int = 0,
    client_updated_at: datetime | None = None,
) -> LessonProgress:
    now = datetime.now(timezone.utc)
    if status == "Completed" and completed_at is None:
        completed_at = now

    progress = get_lesson_progress(db, user_id, lesson_id)

    if progress is None:
        progress = LessonProgress(
            user_id=user_id,
            lesson_id=lesson_id,
            completion_percentage=completion_percentage,
            status=status,
            last_accessed=last_accessed,
            completed_at=completed_at,
            time_spent_seconds=time_spent_seconds,
            client_updated_at=client_updated_at or now,
        )
        db.add(progress)
    else:
        progress.completion_percentage = completion_percentage
        progress.status = status
        if last_accessed is not None:
            progress.last_accessed = last_accessed
        if completed_at is not None:
            progress.completed_at = completed_at
        progress.time_spent_seconds += time_spent_seconds
        progress.client_updated_at = client_updated_at or now

    db.flush()
    db.refresh(progress)
    return progress


def list_lesson_progress(
    db: Session,
    user_id: uuid.UUID,
) -> list[LessonProgress]:
    statement = select(LessonProgress).where(LessonProgress.user_id == user_id)
    return list(db.scalars(statement))

# ══════════════════════════════════════════════════════════════════════
# user_statistics
# ══════════════════════════════════════════════════════════════════════

def get_user_statistics(
    db: Session,
    user_id: uuid.UUID,
) -> UserStatistics | None:
    return db.get(UserStatistics, user_id)


def rebuild_user_statistics(
    db: Session,
    user_id: uuid.UUID | None = None,
) -> None:
    """
    Rebuild user statistics from the live view.
    This should be called if the cached statistics drift from reality.
    """
    if user_id is not None:
        query = text("""
            INSERT INTO user_statistics (
                user_id, lessons_completed, quizzes_completed, minigames_completed,
                total_quiz_score, total_minigame_score, average_accuracy,
                total_time_spent_seconds, updated_at)
            SELECT user_id, lessons_completed, quizzes_completed, minigames_completed,
                   total_quiz_score, total_minigame_score, average_accuracy,
                   total_time_spent_seconds, CURRENT_TIMESTAMP
            FROM v_user_statistics_live
            WHERE user_id = :user_id
            ON CONFLICT (user_id) DO UPDATE SET
                lessons_completed = excluded.lessons_completed,
                quizzes_completed = excluded.quizzes_completed,
                minigames_completed = excluded.minigames_completed,
                total_quiz_score = excluded.total_quiz_score,
                total_minigame_score = excluded.total_minigame_score,
                average_accuracy = excluded.average_accuracy,
                total_time_spent_seconds = excluded.total_time_spent_seconds,
                updated_at = CURRENT_TIMESTAMP
        """)
        db.execute(query, {"user_id": user_id.hex})
    else:
        query = text("""
            INSERT INTO user_statistics (
                user_id, lessons_completed, quizzes_completed, minigames_completed,
                total_quiz_score, total_minigame_score, average_accuracy,
                total_time_spent_seconds, updated_at)
            SELECT user_id, lessons_completed, quizzes_completed, minigames_completed,
                   total_quiz_score, total_minigame_score, average_accuracy,
                   total_time_spent_seconds, CURRENT_TIMESTAMP
            FROM v_user_statistics_live
            ON CONFLICT (user_id) DO UPDATE SET
                lessons_completed = excluded.lessons_completed,
                quizzes_completed = excluded.quizzes_completed,
                minigames_completed = excluded.minigames_completed,
                total_quiz_score = excluded.total_quiz_score,
                total_minigame_score = excluded.total_minigame_score,
                average_accuracy = excluded.average_accuracy,
                total_time_spent_seconds = excluded.total_time_spent_seconds,
                updated_at = CURRENT_TIMESTAMP
        """)
        db.execute(query)

    db.commit()

# ══════════════════════════════════════════════════════════════════════
# streaks
# ══════════════════════════════════════════════════════════════════════

def get_streak(db: Session, user_id: uuid.UUID) -> Streak | None:
    return db.get(Streak, user_id)


def create_or_update_streak(
    db: Session,
    user_id: uuid.UUID,
    current_streak: int | None = None,
    longest_streak: int | None = None,
    last_activity_date: date | None = None,
) -> Streak:
    streak = get_streak(db, user_id)

    if streak is None:
        streak = Streak(
            user_id=user_id,
            current_streak=current_streak or 0,
            longest_streak=longest_streak or 0,
            last_activity_date=last_activity_date,
        )
        db.add(streak)
    else:
        if current_streak is not None:
            streak.current_streak = current_streak
        if longest_streak is not None:
            streak.longest_streak = longest_streak
        if last_activity_date is not None:
            streak.last_activity_date = last_activity_date

    db.commit()
    db.refresh(streak)
    return streak

# ══════════════════════════════════════════════════════════════════════
# leaderboard_cache
# ══════════════════════════════════════════════════════════════════════

def get_leaderboard_cache(
    db: Session,
    board_code: str = "all_time",
    user_id: uuid.UUID | None = None,
) -> LeaderboardCache | None:
    if user_id is not None:
        return db.get(LeaderboardCache, (board_code, user_id))
    return None


def create_or_update_leaderboard_cache(
    db: Session,
    board_code: str,
    user_id: uuid.UUID,
    display_name: str,
    total_score: int,
    rank_position: int,
    current_streak: int = 0,
    badge_count: int = 0,
) -> LeaderboardCache:
    cache = get_leaderboard_cache(db, board_code, user_id)

    if cache is None:
        cache = LeaderboardCache(
            board_code=board_code,
            user_id=user_id,
            display_name=display_name,
            total_score=total_score,
            rank_position=rank_position,
            current_streak=current_streak,
            badge_count=badge_count,
            fetched_at=datetime.now(timezone.utc),
        )
        db.add(cache)
    else:
        cache.display_name = display_name
        cache.total_score = total_score
        cache.rank_position = rank_position
        cache.current_streak = current_streak
        cache.badge_count = badge_count
        cache.fetched_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(cache)
    return cache


def list_leaderboard_cache(
    db: Session,
    board_code: str = "all_time",
    limit: int = 100,
) -> list[LeaderboardCache]:
    statement = (
        select(LeaderboardCache)
        .where(LeaderboardCache.board_code == board_code)
        .order_by(LeaderboardCache.rank_position)
        .limit(limit)
    )
    return list(db.scalars(statement))

# ══════════════════════════════════════════════════════════════════════
# quiz_attempts
# ══════════════════════════════════════════════════════════════════════

def upsert_quiz_attempt(
    db: Session,
    user_id: uuid.UUID,
    attempt_id: uuid.UUID,
    quiz_id: int,
    started_at: datetime | None = None,
    completed_at: datetime | None = None,
    score: int | None = None,
    max_score: int | None = None,
    percentage: float | None = None,
    passed: bool | None = None,
    duration_seconds: int | None = None,
    camera_accuracy: float | None = None,
    mc_accuracy: float | None = None,
) -> QuizAttempt:
    fields = dict(
        started_at=started_at, completed_at=completed_at, score=score,
        max_score=max_score, percentage=percentage, passed=passed,
        duration_seconds=duration_seconds, camera_accuracy=camera_accuracy,
        mc_accuracy=mc_accuracy,
    )
    attempt = db.get(QuizAttempt, attempt_id)
    if attempt is None:
        attempt = QuizAttempt(attempt_id=attempt_id, user_id=user_id, quiz_id=quiz_id, **fields)
        db.add(attempt)
    else:
        for key, value in fields.items():
            if value is not None:
                setattr(attempt, key, value)
    db.flush()
    db.refresh(attempt)
    return attempt


# ══════════════════════════════════════════════════════════════════════
# minigame_attempts
# ══════════════════════════════════════════════════════════════════════

def upsert_minigame_attempt(
    db: Session,
    user_id: uuid.UUID,
    game_attempt_id: uuid.UUID,
    minigame_id: int,
    started_at: datetime | None = None,
    completed_at: datetime | None = None,
    score: int | None = None,
    duration_seconds: int | None = None,
    accuracy: float | None = None,
) -> MinigameAttempt:
    attempt = db.get(MinigameAttempt, game_attempt_id)

    if attempt is None:
        attempt = MinigameAttempt(
            game_attempt_id=game_attempt_id,
            user_id=user_id,
            minigame_id=minigame_id,
            started_at=started_at,
            completed_at=completed_at,
            score=score,
            duration_seconds=duration_seconds,
            accuracy=accuracy,
        )
        db.add(attempt)
    else:
        if started_at is not None:
            attempt.started_at = started_at
        if completed_at is not None:
            attempt.completed_at = completed_at
        if score is not None:
            attempt.score = score
        if duration_seconds is not None:
            attempt.duration_seconds = duration_seconds
        if accuracy is not None:
            attempt.accuracy = accuracy

    db.flush()
    db.refresh(attempt)
    return attempt

# ══════════════════════════════════════════════════════════════════════
# dashboard queries
# ══════════════════════════════════════════════════════════════════════

def get_latest_badge(db: Session, user_id: uuid.UUID) -> tuple[Badge, UserBadges] | None:
    row = db.execute(
        select(Badge, UserBadges)
        .join(UserBadges, UserBadges.badge_id == Badge.badge_id)
        .where(UserBadges.user_id == user_id)
        .order_by(UserBadges.unlocked_at.desc())
        .limit(1)
    ).first()
    return (row[0], row[1]) if row else None


def get_current_module(db: Session, user_id: uuid.UUID) -> Module | None:
    """
    1. Module of the most recently accessed 'In Progress' lesson.
    2. Otherwise the first module (by order) that still has an incomplete lesson.
    3. None if the user has completed everything (or there is no content).
    """
    in_progress = db.execute(
        select(Module)
        .join(Lesson, Lesson.parent_module == Module.module_id)
        .join(LessonProgress, LessonProgress.lesson_id == Lesson.lesson_id)
        .where(
            LessonProgress.user_id == user_id,
            LessonProgress.status == "In Progress",
            Module.is_deleted.is_(False),
            Module.is_active.is_(True),
        )
        .order_by(LessonProgress.last_accessed.desc().nulls_last())
        .limit(1)
    ).scalars().first()
    if in_progress is not None:
        return in_progress

    completed_ids = set(db.scalars(
        select(LessonProgress.lesson_id).where(
            LessonProgress.user_id == user_id,
            LessonProgress.status == "Completed",
        )
    ))
    lessons = db.execute(
        select(Lesson.lesson_id, Lesson.parent_module).where(
            Lesson.is_deleted.is_(False), Lesson.is_active.is_(True)
        )
    ).all()
    incomplete_modules = {m for lid, m in lessons if lid not in completed_ids}

    for module in list_modules(db):  # already ordered by module_order
        if module.module_id in incomplete_modules:
            return module
    return None


def get_module_performance(db: Session, user_id: uuid.UUID) -> list[dict]:
    """
    One entry per active module (7 points for the radar chart):
        score = 0.5 * Q + 0.5 * R      (all values 0-100)

    Q = average percentage across the user's completed quiz attempts for the module.
    R = camera recognition accuracy:
          - average camera accuracy from quiz attempts, if any
          - otherwise average accuracy of camera-type minigame attempts
    A missing Q or R counts as 0, so unstarted modules sit at the center.
    """
    quiz_rows = db.execute(
        select(
            Quiz.module_id,
            func.avg(QuizAttempt.percentage),
            func.avg(QuizAttempt.camera_accuracy),
        )
        .join(Quiz, Quiz.quiz_id == QuizAttempt.quiz_id)
        .where(
            QuizAttempt.user_id == user_id,
            QuizAttempt.completed_at.is_not(None),
        )
        .group_by(Quiz.module_id)
    ).all()
    quiz_by_module = {r[0]: r for r in quiz_rows}

    game_rows = db.execute(
        select(Minigame.module_id, func.avg(MinigameAttempt.accuracy))
        .join(Minigame, Minigame.minigame_id == MinigameAttempt.minigame_id)
        .where(
            MinigameAttempt.user_id == user_id,
            MinigameAttempt.completed_at.is_not(None),
            MinigameAttempt.accuracy.is_not(None),
            Minigame.game_type == "camera",
        )
        .group_by(Minigame.module_id)
    ).all()
    game_acc_by_module = {r[0]: r[1] for r in game_rows}

    result = []
    for module in list_modules(db):
        q_row = quiz_by_module.get(module.module_id)
        q = float(q_row[1]) if q_row and q_row[1] is not None else None

        r = None
        if q_row and q_row[2] is not None:
            r = float(q_row[2])
        elif game_acc_by_module.get(module.module_id) is not None:
            r = float(game_acc_by_module[module.module_id])

        score = 0.5 * (q or 0.0) + 0.5 * (r or 0.0)
        result.append({
            "module_id": module.module_id,
            "module_code": module.module_code,
            "title": module.title,
            "quiz_performance": round(q, 1) if q is not None else None,
            "camera_accuracy": round(r, 1) if r is not None else None,
            "score": round(score, 1),
        })
    return result

# ══════════════════════════════════════════════════════════════════════
# offline_auth
# ══════════════════════════════════════════════════════════════════════

def get_offline_auth(db: Session, user_id: uuid.UUID) -> OfflineAuth | None:
    return db.get(OfflineAuth, user_id)


def get_offline_auth_by_email(db: Session, email: str) -> OfflineAuth | None:
    statement = (
        select(OfflineAuth)
        .join(User, User.user_id == OfflineAuth.user_id)
        .where(User.email == normalize_email(email))
    )
    return db.scalar(statement)


def get_offline_auth_by_username(db: Session, username: str) -> OfflineAuth | None:
    statement = (
        select(OfflineAuth)
        .join(User, User.user_id == OfflineAuth.user_id)
        .where(func.lower(User.username) == username.strip().lower())
    )
    return db.scalar(statement)


def get_offline_auth_by_identifier(db: Session, identifier: str) -> OfflineAuth | None:
    """Usernames can't contain '@', so that character decides which lookup to use."""
    if "@" in identifier:
        return get_offline_auth_by_email(db, identifier)
    return get_offline_auth_by_username(db, identifier)


def upsert_offline_auth(
    db: Session,
    user_id: uuid.UUID,
    password_verifier: str,
    last_online_login: datetime,
) -> OfflineAuth:
    """Called after every successful online login. Resets throttling. Flushes only."""
    if not password_verifier:
        raise ValueError("Password verifier cannot be empty")
    offline_auth = db.get(OfflineAuth, user_id)
    if offline_auth is None:
        offline_auth = OfflineAuth(
            user_id=user_id,
            password_verifier=password_verifier,
            last_online_login=last_online_login,
        )
        db.add(offline_auth)
    else:
        offline_auth.password_verifier = password_verifier
        offline_auth.last_online_login = last_online_login
        offline_auth.failed_attempts = 0
        offline_auth.locked_until = None
    db.flush()
    return offline_auth


def record_failed_login_attempt(
    db: Session,
    username: str,
) -> OfflineAuth | None:
    offline_auth = get_offline_auth_by_username(db, username)
    if offline_auth is None:
        return None

    offline_auth.failed_attempts += 1
    db.commit()
    db.refresh(offline_auth)
    return offline_auth


def reset_failed_login_attempts(
    db: Session,
    user_id: uuid.UUID,
) -> OfflineAuth | None:
    offline_auth = get_offline_auth(db, user_id)
    if offline_auth is None:
        return None

    offline_auth.failed_attempts = 0
    offline_auth.locked_until = None
    db.commit()
    db.refresh(offline_auth)
    return offline_auth


def lock_offline_auth(
    db: Session,
    user_id: uuid.UUID,
    lock_until: datetime,
) -> OfflineAuth | None:
    offline_auth = get_offline_auth(db, user_id)
    if offline_auth is None:
        return None

    offline_auth.locked_until = lock_until
    db.commit()
    db.refresh(offline_auth)
    return offline_auth

# ══════════════════════════════════════════════════════════════════════
# sync_queue
# ══════════════════════════════════════════════════════════════════════

EntityType = Literal["quiz_attempt", "minigame_attempt", "lesson_progress"]
Operation = Literal["upsert", "delete"]

def enqueue_sync(
    db: Session,
    sync_id: uuid.UUID,
    user_id: uuid.UUID,
    entity_type: EntityType,
    entity_id: str | int | uuid.UUID,
    payload: dict[str, Any],
    operation: str = "upsert",
) -> SyncQueue:
    if entity_type not in ("quiz_attempt", "minigame_attempt", "lesson_progress"):
        raise ValueError(f"Invalid entity_type: {entity_type}")
    if operation not in ("upsert", "delete"):
        raise ValueError(f"Invalid operation: {operation}")

    entity_id = str(entity_id)
    body = json.dumps(payload)
    pending = db.scalar(
        select(SyncQueue).where(
            SyncQueue.user_id == user_id,
            SyncQueue.entity_type == entity_type,
            SyncQueue.entity_id == entity_id,
            SyncQueue.synced_at.is_(None),
        )
    )
    if pending is not None:          # newer state replaces the pending one
        pending.payload = body
        pending.operation = operation
        pending.retry_count = 0
        pending.last_error = None
        db.flush()
        return pending

    item = SyncQueue(sync_id=sync_id, user_id=user_id, entity_type=entity_type,
                     entity_id=entity_id, operation=operation, payload=body)
    db.add(item)
    db.flush()
    return item

def dequeue_pending_sync(
    db: Session,
    limit: int = 10,
) -> list[SyncQueue]:
    statement = (
        select(SyncQueue)
        .where(SyncQueue.synced_at == None)
        .order_by(SyncQueue.created_at)
        .limit(limit)
    )
    return list(db.scalars(statement))


def mark_synced(
    db: Session,
    sync_id: uuid.UUID,
) -> bool:
    sync_item = db.get(SyncQueue, sync_id)
    if sync_item is None:
        return False

    sync_item.synced_at = datetime.now(timezone.utc)
    sync_item.retry_count = 0
    sync_item.last_error = None
    db.commit()
    return True


def mark_sync_failed(
    db: Session,
    sync_id: uuid.UUID,
    error_message: str,
) -> bool:
    sync_item = db.get(SyncQueue, sync_id)
    if sync_item is None:
        return False

    sync_item.retry_count += 1
    sync_item.last_attempted_at = datetime.now(timezone.utc)
    sync_item.last_error = error_message
    db.commit()
    return True


def get_sync_queue_stats(
    db: Session,
    user_id: uuid.UUID | None = None,
) -> dict:
    query = select(SyncQueue)
    if user_id is not None:
        query = query.where(SyncQueue.user_id == user_id)

    all_items = list(db.scalars(query))
    pending = [i for i in all_items if i.synced_at is None]
    failed = [i for i in pending if i.retry_count > 0]

    return {
        "total": len(all_items),
        "pending": len(pending),
        "failed": len(failed),
    }
