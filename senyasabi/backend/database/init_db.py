"""
Database initialization for SQLite local cache.

This module handles:
- Creating the database file and directory
- Running the schema to create tables
- Seeding initial data
- Tracking schema version for migrations
"""
from pathlib import Path
import sqlite3

from ..config import DATABASE_PATH, DATABASE_URL
from .session import engine, Base


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
        conn.commit()
    finally:
        conn.close()


def initialize_database(force_rebuild: bool = False):
    """
    Initialize the SQLite database with all tables and initial data.

    This should be called on application startup.

    Args:
        force_rebuild: If True, will delete and recreate the database even if it exists.
    """
    print(f"Initializing database at: {DATABASE_PATH}")

    # Ensure directory exists
    ensure_database_directory()

    # Check if database already exists
    db_path = Path(DATABASE_PATH)
    if db_path.exists() and not force_rebuild:
        print("Database already exists. Skipping initialization.")
        return

    # Delete existing database if forcing rebuild
    if db_path.exists() and force_rebuild:
        db_path.unlink()
        print("Deleted existing database for rebuild.")

    # Run schema to create tables
    print("Creating database schema...")
    run_schema_sql()

    # Seed initial content version
    print("Seeding initial data...")
    seed_initial_data()

    print("Database initialization complete.")


def seed_initial_data():
    """Seed initial data required for the application to function."""
    from .session import SessionLocal
    from .models import ContentVersion

    with SessionLocal() as db:
        # Check if content version already exists
        existing = db.query(ContentVersion).filter(ContentVersion.version_number == 1).first()
        if existing is None:
            # Create initial content version
            content_version = ContentVersion(
                version_number=1,
                released_at=None,
                changelog="Initial content version",
                is_published=True,
                is_deleted=False,
            )
            db.add(content_version)
            db.commit()
            print("Created initial content version (v1).")
        else:
            print("Content version already exists.")


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
