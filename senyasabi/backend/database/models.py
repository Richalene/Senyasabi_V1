from datetime import datetime, date, timezone
import enum
import uuid

from sqlalchemy import (
    String,
    Text,
    Integer,
    Boolean,
    text,
    ForeignKey,
    CheckConstraint,
    Float,
    UniqueConstraint,
    Date,
    Index,
    Uuid,
    LargeBinary
)

from sqlalchemy.orm import Mapped, mapped_column, relationship
from .custom_types import UTCDateTime, JsonType
from .session import Base

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

def _updated_at():
    return mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow, nullable=False)

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_users_username_lower", text("lower(username)"), unique=True),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)  
    username: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    display_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    dark_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = _updated_at()
    offline_auth: Mapped["OfflineAuth | None"] = relationship(back_populates="user", uselist=False)
    lesson_progress: Mapped[list["LessonProgress"]] = relationship(back_populates="user")
    quiz_attempts: Mapped[list["QuizAttempt"]] = relationship(back_populates="user")
    minigame_attempts: Mapped[list["MinigameAttempt"]] = relationship(back_populates="user")
    user_badges: Mapped[list["UserBadges"]] = relationship(back_populates="user")
    
class OfflineAuth(Base):
    __tablename__ = "offline_auth"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True,
    )
    password_verifier: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        default=utcnow,
        nullable=False,
    )
    last_online_login: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    failed_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="offline_auth")


class ContentVersion(Base):
    __tablename__ = "content_versions"

    content_version_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    released_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        default=utcnow,
        nullable=False,
    )
    changelog: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_published: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    updated_at: Mapped[datetime] = _updated_at()

    media_files: Mapped[list["MediaFile"]] = relationship(back_populates="content_version_rel")
    modules: Mapped[list["Module"]] = relationship(back_populates="content_version_rel")
    lessons: Mapped[list["Lesson"]] = relationship(back_populates="content_version_rel")
    signs: Mapped[list["Sign"]] = relationship(back_populates="content_version_rel")
    quizzes: Mapped[list["Quiz"]] = relationship(back_populates="content_version_rel")
    minigames: Mapped[list["Minigame"]] = relationship(back_populates="content_version_rel")
    media_cache: Mapped[list["MediaCache"]] = relationship(back_populates="content_version_rel")


class MediaType(str, enum.Enum):
    IMAGE = "Image"
    VIDEO = "Video"


class MediaFile(Base):
    __tablename__ = "media_files"
    __table_args__ = (
        CheckConstraint("media_type IN ('Image', 'Video')", name="ck_media_files_media_type"),
    )

    media_id: Mapped[int] = mapped_column(Integer, primary_key=True)  # server-assigned
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    object_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    media_type: Mapped[str] = mapped_column(Text, nullable=False)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checksum: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)  # SHA-256 digest
    content_version_id: Mapped[int] = mapped_column(
        ForeignKey("content_versions.content_version_id"), nullable=False, index=True)
    updated_at: Mapped[datetime] = _updated_at()
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    content_version_rel: Mapped["ContentVersion"] = relationship(back_populates="media_files")
    sign_links: Mapped[list["SignMedia"]] = relationship(back_populates="media_file")
    lesson_links: Mapped[list["LessonMedia"]] = relationship(back_populates="media_file")
    media_cache: Mapped["MediaCache | None"] = relationship(back_populates="media_file")

class MediaCache(Base):
    __tablename__ = "media_cache"

    media_id: Mapped[int] = mapped_column(
        ForeignKey("media_files.media_id"),
        primary_key=True,
    )
    local_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content_version_id: Mapped[int] = mapped_column(
        ForeignKey("content_versions.content_version_id"),
        nullable=False,
        index=True,
    )
    cached_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        default=utcnow,
        nullable=False,
    )
    checksum: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)

    content_version_rel: Mapped["ContentVersion"] = relationship(back_populates="media_cache")
    media_file: Mapped["MediaFile"] = relationship(back_populates="media_cache")


class Module(Base):
    __tablename__ = "modules"

    module_id: Mapped[int] = mapped_column(Integer, primary_key=True)  # Server-assigned
    module_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    module_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    updated_at: Mapped[datetime] = _updated_at()
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    content_version_id: Mapped[int] = mapped_column(
        ForeignKey("content_versions.content_version_id"),
        nullable=False,
        index=True,
    )

    content_version_rel: Mapped["ContentVersion"] = relationship(back_populates="modules")
    lessons: Mapped[list["Lesson"]] = relationship(back_populates="module")
    quizzes: Mapped[list["Quiz"]] = relationship(back_populates="module")
    minigames: Mapped[list["Minigame"]] = relationship(back_populates="module")


class Lesson(Base):
    __tablename__ = "lessons"

    lesson_id: Mapped[int] = mapped_column(Integer, primary_key=True)  # Server-assigned
    lesson_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_module: Mapped[int] = mapped_column(
        ForeignKey("modules.module_id"),
        index=True,
        nullable=False,
    )
    lesson_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    updated_at: Mapped[datetime] = _updated_at()
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    content_version_id: Mapped[int] = mapped_column(
        ForeignKey("content_versions.content_version_id"),
        nullable=False,
        index=True,
    )

    module: Mapped["Module"] = relationship(back_populates="lessons")
    content_version_rel: Mapped["ContentVersion"] = relationship(back_populates="lessons")
    lesson_signs: Mapped[list["LessonSign"]] = relationship(back_populates="lesson")
    lesson_media: Mapped[list["LessonMedia"]] = relationship(back_populates="lesson")
    lesson_progress: Mapped[list["LessonProgress"]] = relationship(back_populates="lesson")


class Sign(Base):
    __tablename__ = "signs"

    sign_id: Mapped[int] = mapped_column(Integer, primary_key=True)  # server-assigned
    sign_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    recognition_label: Mapped[str] = mapped_column(String(100), nullable=False)
    updated_at: Mapped[datetime] = _updated_at()
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    content_version_id: Mapped[int] = mapped_column(
        ForeignKey("content_versions.content_version_id"), nullable=False, index=True)

    content_version_rel: Mapped["ContentVersion"] = relationship(back_populates="signs")
    lesson_links: Mapped[list["LessonSign"]] = relationship(back_populates="sign")
    media_links: Mapped[list["SignMedia"]] = relationship(back_populates="sign")
    minigame_signs: Mapped[list["MinigameSign"]] = relationship(back_populates="sign")
    quiz_signs: Mapped[list["QuizSign"]] = relationship(back_populates="sign")

class LessonSign(Base):
    __tablename__ = "lesson_signs"

    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.lesson_id"), primary_key=True)
    sign_id: Mapped[int] = mapped_column(ForeignKey("signs.sign_id"), primary_key=True, index=True)
    display_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    updated_at: Mapped[datetime] = _updated_at()
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    content_version_id: Mapped[int] = mapped_column(
        ForeignKey("content_versions.content_version_id"), nullable=False, index=True)

    lesson: Mapped["Lesson"] = relationship(back_populates="lesson_signs")
    sign: Mapped["Sign"] = relationship(back_populates="lesson_links")


class SignMedia(Base):
    __tablename__ = "sign_media"

    sign_id: Mapped[int] = mapped_column(ForeignKey("signs.sign_id"), primary_key=True)
    media_id: Mapped[int] = mapped_column(ForeignKey("media_files.media_id"), primary_key=True)
    media_role: Mapped[str] = mapped_column(Text, primary_key=True, default="demonstration")
    display_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    updated_at: Mapped[datetime] = _updated_at()
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    content_version_id: Mapped[int] = mapped_column(
        ForeignKey("content_versions.content_version_id"), nullable=False, index=True)

    sign: Mapped["Sign"] = relationship(back_populates="media_links")
    media_file: Mapped["MediaFile"] = relationship(back_populates="sign_links")

class LessonMedia(Base):
    __tablename__ = "lesson_media"

    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.lesson_id"), primary_key=True)
    media_id: Mapped[int] = mapped_column(ForeignKey("media_files.media_id"), primary_key=True)
    media_role: Mapped[str] = mapped_column(Text, primary_key=True)
    display_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    updated_at: Mapped[datetime] = _updated_at()
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    content_version_id: Mapped[int] = mapped_column(
        ForeignKey("content_versions.content_version_id"), nullable=False, index=True)

    lesson: Mapped["Lesson"] = relationship(back_populates="lesson_media")
    media_file: Mapped["MediaFile"] = relationship(back_populates="lesson_links")

class Quiz(Base):
    __tablename__ = "quizzes"

    quiz_id: Mapped[int] = mapped_column(Integer, primary_key=True)  # server-assigned
    quiz_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("modules.module_id"), nullable=False, index=True)
    category_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    passing_score: Mapped[int] = mapped_column(Integer, default=70, nullable=False)
    time_limit_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    config: Mapped[dict] = mapped_column(JsonType, nullable=False, default=dict)  # shuffle, question_types
    updated_at: Mapped[datetime] = _updated_at()
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    content_version_id: Mapped[int] = mapped_column(
        ForeignKey("content_versions.content_version_id"), nullable=False, index=True)

    module: Mapped["Module"] = relationship(back_populates="quizzes")
    content_version_rel: Mapped["ContentVersion"] = relationship(back_populates="quizzes")
    attempts: Mapped[list["QuizAttempt"]] = relationship(back_populates="quiz")
    quiz_signs: Mapped[list["QuizSign"]] = relationship(back_populates="quiz")

class QuizSign(Base):
    __tablename__ = "quiz_signs"

    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.quiz_id"), primary_key=True)
    sign_id: Mapped[int] = mapped_column(ForeignKey("signs.sign_id"), primary_key=True)
    display_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    updated_at: Mapped[datetime] = _updated_at()
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    content_version_id: Mapped[int] = mapped_column(
        ForeignKey("content_versions.content_version_id"), nullable=False, index=True)

    quiz: Mapped["Quiz"] = relationship(back_populates="quiz_signs")
    sign: Mapped["Sign"] = relationship(back_populates="quiz_signs")

class Minigame(Base):
    __tablename__ = "minigames"

    minigame_id: Mapped[int] = mapped_column(Integer, primary_key=True)  # Server-assigned
    minigame_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    game_name: Mapped[str] = mapped_column(String(100), nullable=False)
    game_type: Mapped[str] = mapped_column(String(50), nullable=False)
    module_id: Mapped[int] = mapped_column(
        ForeignKey("modules.module_id"),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    config: Mapped[dict] = mapped_column(JsonType, nullable=False, default=dict)
    updated_at: Mapped[datetime] = _updated_at()
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    content_version_id: Mapped[int] = mapped_column(
        ForeignKey("content_versions.content_version_id"),
        nullable=False,
        index=True,
    )

    module: Mapped["Module"] = relationship(back_populates="minigames")
    content_version_rel: Mapped["ContentVersion"] = relationship(back_populates="minigames")
    attempts: Mapped[list["MinigameAttempt"]] = relationship(back_populates="minigame")
    minigame_signs: Mapped[list["MinigameSign"]] = relationship(back_populates="minigame")


class MinigameSign(Base):
    __tablename__ = "minigame_signs"

    minigame_id: Mapped[int] = mapped_column(
        ForeignKey("minigames.minigame_id"),
        primary_key=True,
    )
    sign_id: Mapped[int] = mapped_column(
        ForeignKey("signs.sign_id"),
        primary_key=True,
    )
    updated_at: Mapped[datetime] = _updated_at()
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    content_version_id: Mapped[int] = mapped_column(
        ForeignKey("content_versions.content_version_id"), nullable=False, index=True)

    minigame: Mapped["Minigame"] = relationship(back_populates="minigame_signs")
    sign: Mapped["Sign"] = relationship(back_populates="minigame_signs")


class Badge(Base):
    __tablename__ = "badges"

    badge_id: Mapped[int] = mapped_column(Integer, primary_key=True)  # Server-assigned
    badge_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    badge_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    user_badges: Mapped[list["UserBadges"]] = relationship(back_populates="badge")


class UserBadges(Base):
    __tablename__ = "user_badges"

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.user_id"), primary_key=True)
    badge_id: Mapped[int] = mapped_column(Integer, ForeignKey("badges.badge_id"), primary_key=True)
    unlocked_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="user_badges")
    badge: Mapped["Badge"] = relationship(back_populates="user_badges")


class LessonProgress(Base):
    __tablename__ = "lesson_progress"
    __table_args__ = (
        CheckConstraint("status <> 'Completed' OR completed_at IS NOT NULL",
            name="ck_lesson_progress_completed_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.user_id"),
        nullable=False,
        primary_key=True,
    )
    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.lesson_id"),
        nullable=False,
        primary_key=True,
    )
    completion_percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(
        Text,
        default="Not Started",
        nullable=False,
    )
    last_accessed: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    client_updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = _updated_at()

    user: Mapped["User"] = relationship(back_populates="lesson_progress")
    lesson: Mapped["Lesson"] = relationship(back_populates="lesson_progress")


class UserStatistics(Base):
    __tablename__ = "user_statistics"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.user_id"),
        primary_key=True,
    )
    lessons_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quizzes_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    minigames_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_quiz_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_minigame_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    average_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_time_spent_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = _updated_at()


class Streak(Base):
    __tablename__ = "streaks"
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.user_id"), primary_key=True)
    current_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_activity_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    updated_at: Mapped[datetime] = _updated_at()


class LeaderboardCache(Base):
    __tablename__ = "leaderboard_cache"
    __table_args__ = (
        Index("idx_leaderboard_cache_rank", "board_code", "rank_position"),
    )

    board_code: Mapped[str] = mapped_column(String(50), primary_key=True, default="all_time")
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.user_id"),
        primary_key=True,
    )
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    total_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rank_position: Mapped[int] = mapped_column(Integer, nullable=False)
    current_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    badge_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fetched_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    __table_args__ = (
        Index("idx_quiz_attempts_user_id", "user_id"),
        Index("idx_quiz_attempts_quiz_id", "quiz_id"),
        Index("idx_quiz_attempts_user_quiz", "user_id", "quiz_id"),
    )

    attempt_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.user_id"),
        nullable=False,
    )
    quiz_id: Mapped[int] = mapped_column(
        ForeignKey("quizzes.quiz_id"),
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    camera_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    mc_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)

    user: Mapped["User"] = relationship(back_populates="quiz_attempts")
    quiz: Mapped["Quiz"] = relationship(back_populates="attempts")


class MinigameAttempt(Base):
    __tablename__ = "minigame_attempts"
    __table_args__ = (
        Index("idx_minigame_attempts_user_id", "user_id"),
        Index("idx_minigame_attempts_minigame_id", "minigame_id"),
        Index("idx_minigame_attempts_user_minigame", "user_id", "minigame_id"),
    )

    game_attempt_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True) 
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.user_id"),
        nullable=False,
    )
    minigame_id: Mapped[int] = mapped_column(
        ForeignKey("minigames.minigame_id"),
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)

    user: Mapped["User"] = relationship(
        back_populates="minigame_attempts",
    )
    minigame: Mapped["Minigame"] = relationship(
        back_populates="attempts",
    )


class SyncQueue(Base):
    __tablename__ = "sync_queue"
    __table_args__ = (
        Index("uq_sync_pending", "user_id", "entity_type", "entity_id",
            unique=True, sqlite_where=text("synced_at IS NULL")),
        CheckConstraint(
            "entity_type IN ('quiz_attempt', 'minigame_attempt', 'lesson_progress')",
            name="ck_sync_queue_entity_type",
        ),
        CheckConstraint(
            "operation IN ('upsert', 'delete')",
            name="ck_sync_queue_operation",
        ),
    )

    sync_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)  
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)  # Server-assigned UUID
    operation: Mapped[str] = mapped_column(String(20), nullable=False, default="upsert")
    payload: Mapped[str] = mapped_column(Text, nullable=False)  # JSON with full entity data
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        default=utcnow,
        nullable=False,
    )
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_attempted_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    synced_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)

