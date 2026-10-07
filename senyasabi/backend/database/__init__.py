from .engine import engine
from .models import *
from .session import Base, SessionLocal


def initialize_database() -> None:
    """
    Create mapped tables if they do not already exist.

    This is suitable for initial development. For production changes,
    use Alembic migrations instead.
    """
    Base.metadata.create_all(bind=engine)
