from datetime import datetime, date
import enum
from uuid import UUID, uuid4

from sqlalchemy import (
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Float,
    UniqueConstraint,
    Date,
    Index,
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .session import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # Autoincrement for offline, server-assigned when synced
    username: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    display_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    offline_auth: Mapped["OfflineAuth | None"] = relationship(back_populates="user", uselist=False)
    lesson_progress: Mapped[list["LessonProgress"]] = relationship(back_populates="user")
    quiz_attempts: Mapped[list["QuizAttempt"]] = relationship(back_populates="user")
    minigame_attempts: Mapped[list["MinigameAttempt"]] = relationship(back_populates="user")
    user_badges: Mapped[list["UserBadges"]] = relationship(back_populates="user")


class OfflineAuth(Base):
    __tablename__ = "offline_auth"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id"),
        primary_key=True,
    )
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    password_verifier: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False,
    )
    last_online_login: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    failed_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="offline_auth")


class ContentVersion(Base):
    __tablename__ = "content_versions"

    content_version_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    released_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
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

    media_id: Mapped[int] = mapped_column(Integer, primary_key=True)  # Server-assigned
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    object_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    media_type: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checksum: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_version: Mapped[int] = mapped_column(
        ForeignKey("content_versions.content_version_id"),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    content_version_rel: Mapped["ContentVersion"] = relationship(back_populates="media_files")
    sign: Mapped["Sign | None"] = relationship(back_populates="media_file")
    media_cache: Mapped["MediaCache | None"] = relationship(back_populates="media_file")


class MediaCache(Base):
    __tablename__ = "media_cache"

    media_id: Mapped[int] = mapped_column(
        ForeignKey("media_files.media_id"),
        primary_key=True,
    )
    local_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content_version: Mapped[int] = mapped_column(
        ForeignKey("content_versions.content_version_id"),
        nullable=False,
        index=True,
    )
    cached_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False,
    )
    checksum: Mapped[str | None] = mapped_column(Text, nullable=True)

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
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    content_version: Mapped[int] = mapped_column(
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
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    content_version: Mapped[int] = mapped_column(
        ForeignKey("content_versions.content_version_id"),
        nullable=False,
        index=True,
    )

    module: Mapped["Module"] = relationship(back_populates="lessons")
    content_version_rel: Mapped["ContentVersion"] = relationship(back_populates="lessons")
    signs: Mapped[list["Sign"]] = relationship(back_populates="lesson")
    lesson_progress: Mapped[list["LessonProgress"]] = relationship(back_populates="lesson")


class Sign(Base):
    __tablename__ = "signs"

    sign_id: Mapped[int] = mapped_column(Integer, primary_key=True)  # Server-assigned
    sign_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.lesson_id"),
        nullable=False,
        index=True,
    )
    media_id: Mapped[int] = mapped_column(
        ForeignKey("media_files.media_id"),
        unique=True,
        nullable=False,
    )
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    recognition_label: Mapped[str] = mapped_column(String(100), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    content_version: Mapped[int] = mapped_column(
        ForeignKey("content_versions.content_version_id"),
        nullable=False,
        index=True,
    )

    lesson: Mapped["Lesson"] = relationship(back_populates="signs")
    media_file: Mapped["MediaFile"] = relationship(back_populates="sign")
    content_version_rel: Mapped["ContentVersion"] = relationship(back_populates="signs")
    minigame_signs: Mapped[list["MinigameSign"]] = relationship(back_populates="sign")


class Quiz(Base):
    __tablename__ = "quizzes"

    quiz_id: Mapped[int] = mapped_column(Integer, primary_key=True)  # Server-assigned
    module_id: Mapped[int] = mapped_column(
        ForeignKey("modules.module_id"),
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    passing_score: Mapped[int] = mapped_column(
        Integer,
        default=70,
        nullable=False,
    )
    time_limit_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    content_version: Mapped[int] = mapped_column(
        ForeignKey("content_versions.content_version_id"),
        nullable=False,
        index=True,
    )

    module: Mapped["Module"] = relationship(back_populates="quizzes")
    content_version_rel: Mapped["ContentVersion"] = relationship(back_populates="quizzes")
    attempts: Mapped[list["QuizAttempt"]] = relationship(back_populates="quiz")


class Minigame(Base):
    __tablename__ = "minigames"

    minigame_id: Mapped[int] = mapped_column(Integer, primary_key=True)  # Server-assigned
    minigame_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    game_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    game_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    module_id: Mapped[int] = mapped_column(
        ForeignKey("modules.module_id"),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    config: Mapped[str] = mapped_column(Text, nullable=False)  # JSON stored as TEXT
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    content_version: Mapped[int] = mapped_column(
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

    minigame: Mapped["Minigame"] = relationship(back_populates="minigame_signs")
    sign: Mapped["Sign"] = relationship(back_populates="minigame_signs")


class Badge(Base):
    __tablename__ = "badges"

    badge_id: Mapped[int] = mapped_column(Integer, primary_key=True)  # Server-assigned
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

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id"), primary_key=True)
    badge_id: Mapped[int] = mapped_column(Integer, ForeignKey("badges.badge_id"), primary_key=True)
    unlocked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)

    user: Mapped["User"] = relationship(back_populates="user_badges")
    badge: Mapped["Badge"] = relationship(back_populates="user_badges")


class LessonProgress(Base):
    __tablename__ = "lesson_progress"
    __table_args__ = (
        CheckConstraint(
            "status IN ('Not Started', 'In Progress', 'Completed')",
            name="ck_lesson_progress_status",
        ),
    )

    user_id: Mapped[int] = mapped_column(
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
    last_accessed: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="lesson_progress")
    lesson: Mapped["Lesson"] = relationship(back_populates="lesson_progress")


class UserStatistics(Base):
    __tablename__ = "user_statistics"

    user_id: Mapped[int] = mapped_column(
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
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False,
    )


class Streak(Base):
    __tablename__ = "streaks"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_streaks_user_id"),
    )

    streak_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id"),
        nullable=False,
        unique=True,
    )
    current_streak: Mapped[int | None] = mapped_column(Integer, nullable=True)
    longest_streak: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_activity_date: Mapped[date | None] = mapped_column(Date, nullable=True)


class LeaderboardCache(Base):
    __tablename__ = "leaderboard_cache"
    __table_args__ = (
        Index("idx_leaderboard_cache_rank", "board_code", "rank_position"),
    )

    board_code: Mapped[str] = mapped_column(String(50), primary_key=True, default="all_time")
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id"),
        primary_key=True,
    )
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    total_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rank_position: Mapped[int] = mapped_column(Integer, nullable=False)
    current_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    badge_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    __table_args__ = (
        Index("idx_quiz_attempts_user_id", "user_id"),
        Index("idx_quiz_attempts_quiz_id", "quiz_id"),
        Index("idx_quiz_attempts_user_quiz", "user_id", "quiz_id"),
    )

    attempt_id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID as string
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id"),
        nullable=False,
    )
    quiz_id: Mapped[int] = mapped_column(
        ForeignKey("quizzes.quiz_id"),
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    user: Mapped["User"] = relationship(back_populates="quiz_attempts")
    quiz: Mapped["Quiz"] = relationship(back_populates="attempts")


class MinigameAttempt(Base):
    __tablename__ = "minigame_attempts"
    __table_args__ = (
        Index("idx_minigame_attempts_user_id", "user_id"),
        Index("idx_minigame_attempts_minigame_id", "minigame_id"),
        Index("idx_minigame_attempts_user_minigame", "user_id", "minigame_id"),
    )

    game_attempt_id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID as string
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id"),
        nullable=False,
    )
    minigame_id: Mapped[int] = mapped_column(
        ForeignKey("minigames.minigame_id"),
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
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
        UniqueConstraint("entity_type", "entity_id", name="uq_sync_pending"),
        CheckConstraint(
            "entity_type IN ('quiz_attempt', 'minigame_attempt', 'lesson_completion')",
            name="ck_sync_queue_entity_type",
        ),
        CheckConstraint(
            "operation IN ('upsert', 'delete')",
            name="ck_sync_queue_operation",
        ),
    )

    sync_id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID as string
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)  # Server-assigned UUID
    operation: Mapped[str] = mapped_column(String(20), nullable=False, default="upsert")
    payload: Mapped[str] = mapped_column(Text, nullable=False)  # JSON with full entity data
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False,
    )
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_attempted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
