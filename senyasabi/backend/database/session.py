from collections.abc import Generator

from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .engine import engine


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass

# creates orm sessions
SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


def get_session() -> Generator[Session, None, None]:
    """
    Provide a database session and guarantee that it is closed.

    This generator is useful for service functions, tests, or dependency
    injection.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()