from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import *

"""
--------------------- EXAMPLES ---------------------
these are sample operations for my reference

def create_user(db: Session, username: str) -> User:
    username = username.strip()

    if not username:
        raise ValueError("Username cannot be empty")

    user = User(username=username)
    db.add(user)
    db.commit()
    db.refresh(user)

    return user

def get_user(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)

def get_user_by_username(
    db: Session,
    username: str,
) -> User | None:
    statement = select(User).where(User.username == username)
    return db.scalar(statement)

def update_username(
    db: Session,
    user_id: int,
    new_username: str,
) -> User | None:
    user = db.get(User, user_id)

    if user is None:
        return None

    new_username = new_username.strip()

    if not new_username:
        raise ValueError("Username cannot be empty")

    user.username = new_username
    db.commit()
    db.refresh(user)

    return user

def delete_user(db: Session, user_id: int) -> bool:
    user = db.get(User, user_id)

    if user is None:
        return False

    db.delete(user)
    db.commit()
    return True

def start_lesson_session(
    db: Session,
    user_id: int,
    mode: str,
    total: int,
    lesson_name: str | None = None,
    category: str | None = None,
) -> LessonSession:
    lesson_session = LessonSession(
        user_id=user_id,
        mode=mode,
        total=total,
        lesson_name=lesson_name,
        category=category,
    )

    db.add(lesson_session)
    db.commit()
    db.refresh(lesson_session)

    return lesson_session

def record_attempt(
    db: Session,
    session_id: int,
    target: str,
    predicted: str | None,
    confidence: float | None,
    result: str,
) -> LessonAttempt:
    attempt = LessonAttempt(
        session_id=session_id,
        target=target,
        predicted=predicted,
        confidence=confidence,
        result=result,
    )

    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return attempt

def finish_lesson_session(
    db: Session,
    session_id: int,
    score: int,
    total: int,
) -> LessonSession | None:
    lesson_session = db.get(LessonSession, session_id)

    if lesson_session is None:
        return None

    lesson_session.score = score
    lesson_session.total = total
    lesson_session.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(lesson_session)

    return lesson_session

def complete_lesson(
    db: Session,
    session_id: int,
    score: int,
    total: int,
) -> LessonSession | None:
    lesson_session = db.get(LessonSession, session_id)

    if lesson_session is None:
        return None

    try:
        lesson_session.score = score
        lesson_session.total = total
        lesson_session.completed_at = datetime.utcnow()

        # Add any related progress updates here.

        db.commit()
        db.refresh(lesson_session)
        return lesson_session

    except Exception:
        db.rollback()
        raise
        
"""

# ══════════════════════════════════════════════════════════════════════
# users
# ══════════════════════════════════════════════════════════════════════

def create_user(
    db: Session,
    username: str,
    email: str,
    password_hash: str,
    display_name: str | None = None,
) -> User:
    if not username.strip():
        raise ValueError("Username is required")
    if not email.strip():
        raise ValueError("Email is required")
    if not password_hash:
        raise ValueError("Password is required")

    user = User(
        username=username,
        email=email,
        password_hash=password_hash,
        display_name=display_name,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_user_by_username(db: Session, username: str) -> User | None:
    statement = select(User).where(User.username == username)
    return db.scalar(statement)


def get_user_by_email(db: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    return db.scalar(statement)


def update_user_profile(
    db: Session,
    user_id: int,
    display_name: str | None = None,
    email: str | None = None,
) -> User | None:
    user = db.get(User, user_id)

    if user is None:
        return None

    if display_name is not None:
        user.display_name = display_name
    if email is not None:
        user.email = email

    db.commit()
    db.refresh(user)

    return user


def update_user_password(
    db: Session,
    user_id: int,
    new_password_hash: str,
) -> User | None:
    user = db.get(User, user_id)
    
    if user is None:
        return None

    new_password_hash = new_password_hash.strip()

    if not new_password_hash:
        raise ValueError("Password cannot be empty")

    user.password_hash = new_password_hash
    db.commit()
    db.refresh(user)
    
    return user


def update_user_settings(
    db: Session,
    user_id: int,
    notifications_enabled: bool | None = None,
    dark_mode: bool | None = None,
) -> User | None:
    user = db.get(User, user_id)

    if user is None:
        return None
    if notifications_enabled is not None:
        user.notifications_enabled = notifications_enabled
    if dark_mode is not None:
        user.dark_mode = dark_mode

    db.commit()
    db.refresh(user)

    return user


def delete_user(db: Session, user_id: int) -> bool:
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
    changelog: str | None = None,
    is_published: bool = False,
) -> ContentVersion:
    if changelog is not None:
        changelog = changelog.strip()

    content_version = ContentVersion(
        changelog=changelog,
        is_published=is_published,
    )

    db.add(content_version)
    db.commit()
    db.refresh(content_version)

    return content_version


def get_content_version(
    db: Session,
    version_id: int,
) -> ContentVersion | None:
    return db.get(ContentVersion, version_id)


def update_content_version(
    db: Session,
    version_id: int,
    **fields,
) -> ContentVersion | None:
    content_version = db.get(ContentVersion, version_id)

    if content_version is None:
        return None

    allowed_fields = {
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
    version_id: int,
) -> bool:
    content_version = db.get(ContentVersion, version_id)

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
    file_name: str,
    storage_path: str,
    media_type: str,
    width: int | None = None,
    height: int | None = None,
    duration_seconds: float | None = None,
    file_size: int | None = None,
) -> MediaFile:
    file_name = file_name.strip()
    storage_path = storage_path.strip()
    media_type = media_type.strip()

    if not file_name:
        raise ValueError("File name cannot be empty")
    if not storage_path:
        raise ValueError("Storage path cannot be empty")
    if media_type not in ("Image", "Video"):
        raise ValueError("media_type must be 'Image' or 'Video'")

    media_file = MediaFile(
        file_name=file_name,
        storage_path=storage_path,
        media_type=media_type,
        width=width,
        height=height,
        duration_seconds=duration_seconds,
        file_size=file_size,
    )

    db.add(media_file)
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
        "storage_path",
        "local_cache_path",
        "media_type",
        "width",
        "height",
        "duration_seconds",
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
# modules
# ══════════════════════════════════════════════════════════════════════

def create_module(
    db: Session,
    title: str,
    content_version: int,
    module_order: int,
    description: str | None = None,
) -> Module:
    title = title.strip()

    if not title:
        raise ValueError("Title cannot be empty")
    if not module_order:
        raise ValueError("Module order cannot be empty")
    if not content_version:
        raise ValueError("Content version cannot be empty")
    if description is not None:
        description = description.strip()

    module = Module(
        title=title,
        description=description,
        module_order=module_order,
        content_version=content_version,
    )

    db.add(module)
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
    title: str,
    content_version: int,
    parent_module: int,
    lesson_order: int,
    description: str | None = None,
) -> Lesson:
    title = title.strip()

    if not title:
        raise ValueError("title cannot be empty")
    if not parent_module:
        raise ValueError("parent_module cannot be empty")
    if not content_version:
        raise ValueError("content_version cannot be empty")
    if not lesson_order:
        raise ValueError("lesson_order cannot be empty")
    if description is not None:
        description = description.strip()

    lesson = Lesson(
        title=title,
        description=description,
        parent_module=parent_module,
        lesson_order=lesson_order,
        content_version=content_version,
    )

    db.add(lesson)
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
        "title",
        "description",
        "lesson_order",
        "parent_module,"
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
    lesson_id: int,
    media_id: int,
    sign_translation: str,
    content_version: int,
) -> Sign:
    sign_translation = sign_translation.strip()

    if not sign_translation:
        raise ValueError("Sign translation cannot be empty")

    existing = db.query(Sign).filter(Sign.media_id == media_id).first()
    if existing is not None:
        raise ValueError(f"media_id {media_id} is already linked to another sign")

    sign = Sign(
        lesson_id=lesson_id,
        media_id=media_id,
        sign_translation=sign_translation,
        content_version=content_version,
    )

    db.add(sign)
    db.commit()
    db.refresh(sign)

    return sign


def get_sign(
    db: Session,
    sign_id: int,
) -> Sign | None:
    return db.get(Sign, sign_id)


def list_signs(
    db: Session,
    lesson_id: int | None = None,
) -> list[Sign]:
    query = db.query(Sign).filter(Sign.is_deleted == False)

    if lesson_id is not None:
        query = query.filter(Sign.lesson_id == lesson_id)

    return query.all()


def update_sign(
    db: Session,
    sign_id: int,
    **fields,
) -> Sign | None:
    sign = db.get(Sign, sign_id)

    if sign is None:
        return None

    allowed_fields = {
        "lesson_id",
        "media_id",
        "sign_translation",
        "content_version",
    }

    for key, value in fields.items():
        if key not in allowed_fields:
            raise ValueError(f"Cannot update field: {key}")

        if key == "sign_translation":
            value = value.strip()
            if not value:
                raise ValueError("Sign translation cannot be empty")

        if key == "media_id":
            existing = (
                db.query(Sign)
                .filter(Sign.media_id == value, Sign.sign_id != sign_id)
                .first()
            )
            if existing is not None:
                raise ValueError(f"media_id {value} is already linked to another sign")

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
    module_id: int,
    content_version: int,
    title: str | None = None,
    passing_score: int = 70,
    time_limit_seconds: int | None = None,
) -> Quiz:
    if title is not None:
        title = title.strip()
        if not title:
            title = None
    if not (0 <= passing_score <= 100):
        raise ValueError("passing_score must be between 0 and 100")
    if time_limit_seconds is not None and time_limit_seconds <= 0:
        raise ValueError("time_limit_seconds must be positive")

    quiz = Quiz(
        module_id=module_id,
        title=title,
        passing_score=passing_score,
        time_limit_seconds=time_limit_seconds,
        content_version=content_version,
    )

    db.add(quiz)
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
    lesson_id: int,
    content_version: int,
    game_name: str | None = None,
    game_type: str | None = None,
    description: str | None = None,
) -> Minigame:
    if game_name is not None:
        game_name = game_name.strip()
        if not game_name:
            game_name = None
    if game_type is not None:
        game_type = game_type.strip()
        if not game_type:
            game_type = None
    if description is not None:
        description = description.strip()
        if not description:
            description = None

    minigame = Minigame(
        lesson_id=lesson_id,
        game_name=game_name,
        game_type=game_type,
        description=description,
        content_version=content_version,
    )

    db.add(minigame)
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
    lesson_id: int | None = None,
    game_type: str | None = None,
) -> list[Minigame]:
    query = db.query(Minigame).filter(Minigame.is_deleted == False)

    if lesson_id is not None:
        query = query.filter(Minigame.lesson_id == lesson_id)
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
        "lesson_id",
        "game_name",
        "game_type",
        "description",
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
# badge
# ══════════════════════════════════════════════════════════════════════

def create_badge(
    db: Session,
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
        badge_name=badge_name,
        description=description,
    )

    db.add(badge)
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
    user_id: int,
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
    user_id: int,
    badge_id: int,
) -> UserBadges | None:
    return db.get(UserBadges, (user_id, badge_id))


def list_user_badges(
    db: Session,
    user_id: int,
) -> list[UserBadges]:
    return (
        db.query(UserBadges)
        .filter(UserBadges.user_id == user_id)
        .all()
    )


def revoke_badge(
    db: Session,
    user_id: int,
    badge_id: int,
) -> bool:
    user_badge = db.get(UserBadges, (user_id, badge_id))

    if user_badge is None:
        return False

    db.delete(user_badge)
    db.commit()

    return True

# ══════════════════════════════════════════════════════════════════════
# module_progress
# ══════════════════════════════════════════════════════════════════════
