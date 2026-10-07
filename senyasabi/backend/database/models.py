from datetime import datetime, date
import enum
from decimal import Decimal
from sqlalchemy.dialects.postgresql import UUID
from uuid import UUID, uuid4

from sqlalchemy import (
    String,
    Text,
    Integer,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    CheckConstraint,
    func,
    Numeric,
    UniqueConstraint,
    Date,
    Index,
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .session import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    display_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    notifications_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="1",
        nullable=False,
    )
    dark_mode: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="0",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        server_default=func.now(),
        nullable=False,
    )

    module_progress: Mapped[list["ModuleProgress"]] = relationship(back_populates="user")
    statistics: Mapped[list["UserStatistics"]] = relationship(back_populates="user")
    streaks: Mapped["Streak | None"] = relationship(back_populates="user", uselist=False)
    leaderboard_entries: Mapped["Leaderboard | None"] = relationship(back_populates="user", uselist=False)
    quiz_attempts: Mapped[list["QuizAttempt"]] = relationship(back_populates="user")
    minigame_attempts: Mapped[list["MinigameAttempt"]] = relationship(back_populates="user")
    user_badges: Mapped[list["UserBadges"]] = relationship(back_populates="user")


class ContentVersion(Base):
    __tablename__ = "content_versions"

    version_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    released_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        server_default=func.now(),
        nullable=False,
    )
    changelog: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_published: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="0",
        nullable=False,
    )
    is_deleted: Mapped[bool] = mapped_column(
            Boolean,
            default=False,
            server_default="0",
            nullable=False,
        )

    media_files: Mapped[list["MediaFile"]] = relationship(back_populates="content_version_rel")
    modules: Mapped[list["Module"]] = relationship(back_populates="content_version_rel")
    lessons: Mapped[list["Lesson"]] = relationship(back_populates="content_version_rel")
    signs: Mapped[list["Sign"]] = relationship(back_populates="content_version_rel")
    quizzes: Mapped[list["Quiz"]] = relationship(back_populates="content_version_rel")
    minigames: Mapped[list["Minigame"]] = relationship(back_populates="content_version_rel")

class MediaType(str, enum.Enum):
    IMAGE = "Image"
    VIDEO = "Video"


class MediaFile(Base):
    __tablename__ = "media_files"
    __table_args__ = (
        CheckConstraint("media_type IN ('Image', 'Video')", name="ck_media_files_media_type"),
    )

    media_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    object_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    media_type: Mapped[str] = mapped_column(Text, nullable=False)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    checksum: Mapped[int | None] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        server_default=func.now(),
        nullable=False,
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="0",
        nullable=False,
    )
    content_version: Mapped[int] = mapped_column(
        ForeignKey("content_versions.version_id"),
        nullable=False,
        index=True,
    )

    content_version_rel: Mapped["ContentVersion"] = relationship(back_populates="media_files")
    sign: Mapped["Sign | None"] = relationship(back_populates="media_file")


class MediaCache(Base):
    __tablename__ = "media_cache"

    media_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    local_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content_version: Mapped[int] = mapped_column(
        ForeignKey("content_versions.version_id"),
        nullable=False,
        index=True,
    )
    cached_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        server_default=func.now(),
        nullable=False,
    )
    checksum: Mapped[int | None] = mapped_column(Integer, nullable=False)


    content_version_rel: Mapped["ContentVersion"] = relationship(back_populates="media_files")

class Module(Base):
    __tablename__ = "modules"

    module_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    module_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="1",
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        server_default=func.now(),
        nullable=False,
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="0",
        nullable=False,
    )
    content_version: Mapped[int] = mapped_column(
        ForeignKey("content_versions.version_id"),
        nullable=False,
        index=True,
    )

    content_version_rel: Mapped["ContentVersion"] = relationship(back_populates="modules")
    lessons: Mapped[list["Lesson"]] = relationship(back_populates="module")
    quizzes: Mapped[list["Quiz"]] = relationship(back_populates="module")
    progress_entries: Mapped[list["ModuleProgress"]] = relationship(back_populates="module")


class Lesson(Base):
    __tablename__ = "lessons"

    lesson_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
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
        server_default="1",
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        server_default=func.now(),
        nullable=False,
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="0",
        nullable=False,
    )
    content_version: Mapped[int] = mapped_column(
        ForeignKey("content_versions.version_id"),
        nullable=False,
        index=True,
    )

    module: Mapped["Module"] = relationship(back_populates="lessons")
    content_version_rel: Mapped["ContentVersion"] = relationship(back_populates="lessons")
    signs: Mapped[list["Sign"]] = relationship(back_populates="lesson")
    minigames: Mapped[list["Minigame"]] = relationship(back_populates="lesson")

class Sign(Base):
    __tablename__ = "signs"

    sign_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
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
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        server_default=func.now(),
        nullable=False,
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="0",
        nullable=False,
    )
    content_version: Mapped[int] = mapped_column(
        ForeignKey("content_versions.version_id"),
        nullable=False,
        index=True,
    )

    lesson: Mapped["Lesson"] = relationship(back_populates="signs")
    media_file: Mapped["MediaFile"] = relationship(back_populates="sign")
    content_version_rel: Mapped["ContentVersion"] = relationship(back_populates="signs")


class Quiz(Base):
    __tablename__ = "quizzes"

    quiz_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    module_id: Mapped[int] = mapped_column(
        ForeignKey("modules.module_id"),
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    passing_score: Mapped[int] = mapped_column(
        Integer,
        default=70,
        server_default="70",
        nullable=False,
    )
    time_limit_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        server_default=func.now(),
        nullable=False,
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="0",
        nullable=False,
    )
    content_version: Mapped[int] = mapped_column(
        ForeignKey("content_versions.version_id"),
        nullable=False,
        index=True,
    )

    module: Mapped["Module"] = relationship(back_populates="quizzes")
    content_version_rel: Mapped["ContentVersion"] = relationship(back_populates="quizzes")
    attempts: Mapped[list["QuizAttempt"]] = relationship(back_populates="quiz")

class Minigame(Base):
    __tablename__ = "minigames"

    minigame_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    module_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.lesson_id"),
        nullable=False,
    )
    game_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    game_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        server_default=func.now(),
        nullable=False,
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="0",
        nullable=False,
    )
    content_version: Mapped[int] = mapped_column(
        ForeignKey("content_versions.version_id"),
        nullable=False,
        index=True,
    )

    lesson: Mapped["Lesson"] = relationship(back_populates="minigames")
    content_version_rel: Mapped["ContentVersion"] = relationship(back_populates="minigames")
    attempts: Mapped[list["MinigameAttempt"]] = relationship(back_populates="minigame")

class Badge(Base):
    __tablename__ = "badge"

    badge_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    badge_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="0",
        nullable=False,
    )

    user_badges: Mapped["UserBadges"] = relationship(back_populates="badge")

class UserBadges(Base):
    __tablename__ = "user_badges"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id"), primary_key=True)
    badge_id: Mapped[int] = mapped_column(Integer, ForeignKey("badges.badge_id"), primary_key=True)
    unlocked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)

    user: Mapped["User"] = relationship(back_populates="user_badges")
    badge: Mapped["Badge"] = relationship(back_populates="user_badges")

class ModuleProgress(Base):
    __tablename__ = "module_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "module_id", name="idx_module_progress"),
        CheckConstraint(
            "status IN ('Not Started', 'In Progress', 'Completed')",
            name="ck_module_progress_status",
        ),
    )

    progress_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id"),
        nullable=False,
    )
    module_id: Mapped[int] = mapped_column(
        ForeignKey("modules.module_id"),
        nullable=False,
    )
    completion_percentage: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        Text,
        default="Not Started",
        server_default="Not Started",
        nullable=False,
    )
    last_accessed: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="module_progress")
    module: Mapped["Module"] = relationship(back_populates="progress_entries")


class UserStatistics(Base):
    __tablename__ = "user_statistics"

    stat_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id"),
        nullable=False,
    )
    lessons_completed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quizzes_completed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    minigames_completed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_quiz_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_minigame_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    average_accuracy: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    total_time_spent: Mapped[int | None] = mapped_column(Integer, nullable=True)

    user: Mapped["User"] = relationship(back_populates="statistics")

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

    user: Mapped["User"] = relationship(back_populates="streaks")


class Leaderboard(Base):
    __tablename__ = "leaderboard"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_leaderboard_user_id"),
        Index("idx_leaderboard_rank_position", "rank_position"),
    )
    
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id"),
        nullable=False,
        unique=True,
    )
    total_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    average_accuracy: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    lessons_completed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_streak: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rank_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="leaderboard_entries")

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    __table_args__ = (
        Index("idx_quiz_attempts_user_id", "user_id"),
        Index("idx_quiz_attempts_quiz_id", "quiz_id"),
        Index("idx_quiz_attempts_user_quiz", "user_id", "quiz_id"),
    )

    attempt_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
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
    percentage: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
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

    game_attempt_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
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
    accuracy: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)

    user: Mapped["User"] = relationship(
        back_populates="minigame_attempts",
    )
    minigame: Mapped["Minigame"] = relationship(
        back_populates="attempts",
    )

class SyncQueue(Base):
    __tablename__ = "sync_queue"
    game_attempt_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(default=uuid4, nullable=False)
    operation: Mapped[str] = mapped_column(String(20), nullable=True)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        server_default=func.now(),
        nullable=False,
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_attempted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    synced_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
