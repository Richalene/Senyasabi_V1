"""
Database initialization for SQLite local cache.

This module handles:
- Creating the database file and directory
- Running the schema to create tables
- Seeding initial data
- Tracking schema version for migrations
"""
from pathlib import Path
import shutil
import sqlite3
import logging

from ..config import DATABASE_PATH
from .session import engine, Base
from .migrations import run_migrations, get_migration_status

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 2

def _stored_schema_version(db_path: Path) -> int:
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute("PRAGMA user_version").fetchone()[0]
    finally:
        conn.close()

def ensure_database_directory():
    """Ensure the database directory exists."""
    db_path = Path(DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)


def run_schema_sql():
    """Execute the SQLite schema SQL file to create all tables."""
    schema_path = Path(__file__).parent / "sqlite_schema.sql"

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    # Connect to the database and execute the schema
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        # Execute the schema
        conn.executescript(schema_sql)
        conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        conn.commit()
    finally:
        conn.close()



def initialize_database(force_rebuild: bool = False):
    """
    Initialize the local SQLite database schema.

    Content is populated separately through Supabase synchronization.
    """
    logger.info("Initializing database at: %s", DATABASE_PATH)

    ensure_database_directory()

    db_path = Path(DATABASE_PATH)

    if db_path.exists() and force_rebuild:
        db_path.unlink()
        logger.info("Deleted existing database for rebuild.")

    if not db_path.exists():
        logger.info("Creating database schema...")
        run_schema_sql()

        logger.info("Running initial migrations...")
        run_migrations()

    else:
        logger.info("Database exists. Checking migrations...")
        migration_result = run_migrations()

        if migration_result["success"]:
            logger.info(
                "Migrations completed: %d applied",
                migration_result["applied"]
            )
        else:
            logger.warning(
                "Some migrations failed: %d applied, %d failed",
                migration_result["applied"],
                migration_result["failed"]
            )

    logger.info("Database schema initialization complete.")

def rebuild_database():
    """
    Rebuild the database from scratch.

    WARNING: This will delete all existing data!
    Use only for development/testing.
    """
    print(f"Rebuilding database at: {DATABASE_PATH}")

    # Delete existing database
    db_path = Path(DATABASE_PATH)
    if db_path.exists():
        db_path.unlink()
        print("Deleted existing database.")

    # Reinitialize
    initialize_database()

def has_cached_content() -> bool:
    """Check whether initial content has been synchronized locally."""
    from .session import SessionLocal
    from .models import Module

    with SessionLocal() as db:
        return db.query(Module).first() is not None


def get_schema_version():
    """Get the current schema version from the database."""
    from .session import SessionLocal
    from .models import ContentVersion

    with SessionLocal() as db:
        latest = db.query(ContentVersion).order_by(ContentVersion.version_number.desc()).first()
        if latest:
            return latest.version_number
        return None


if __name__ == "__main__":
    # Allow running this module directly for initialization
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--rebuild":
        rebuild_database()
    else:
        initialize_database()
