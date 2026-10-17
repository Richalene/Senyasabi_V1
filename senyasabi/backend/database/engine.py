from sqlalchemy import create_engine, event

from ..config import SQLITE_URL


engine = create_engine(
    SQLITE_URL,
    echo=False,
    future=True,
)


@event.listens_for(engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    """Enable foreign-key enforcement for every SQLite connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()