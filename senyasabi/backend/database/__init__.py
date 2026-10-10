from .engine import engine
from .models import *
from .session import Base, SessionLocal
from .init_db import initialize_database, rebuild_database, get_schema_version


def initialize_database() -> None:
    """
    Create mapped tables if they do not already exist.

    This is suitable for initial development. For production changes,
    use Alembic migrations instead.
    """
    Base.metadata.create_all(bind=engine)
