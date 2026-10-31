"""
SQLite migration system for SenyaSabi local cache.

This module handles:
- Tracking applied migrations
- Running pending migrations in order
- Providing migration utilities
"""
import logging
import sqlite3
from pathlib import Path
from typing import List, Optional

from ..config import DATABASE_PATH

logger = logging.getLogger(__name__)


MIGRATIONS_DIR = Path(__file__).parent


def get_applied_migrations(conn: sqlite3.Connection) -> set[str]:
    """Get the set of applied migration filenames."""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
    )
    if cursor.fetchone() is None:
        return set()
    
    cursor = conn.execute("SELECT migration FROM schema_migrations ORDER BY applied_at")
    return {row[0] for row in cursor.fetchall()}


def ensure_migrations_table(conn: sqlite3.Connection):
    """Create the schema_migrations table if it doesn't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            migration TEXT NOT NULL UNIQUE,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)


def get_pending_migrations() -> List[Path]:
    """Get list of migration SQL files, sorted by filename."""
    if not MIGRATIONS_DIR.exists():
        logger.warning("Migrations directory does not exist: %s", MIGRATIONS_DIR)
        return []
    
    migrations = sorted(MIGRATIONS_DIR.glob("*.sql"))
    return migrations


def run_migration(conn: sqlite3.Connection, migration_path: Path) -> bool:
    """Run a single migration file."""
    migration_name = migration_path.name
    
    try:
        logger.info("Running migration: %s", migration_name)
        
        with open(migration_path, "r", encoding="utf-8") as f:
            migration_sql = f.read()
        
        # Execute the migration
        conn.executescript(migration_sql)
        
        # Record the migration
        conn.execute(
            "INSERT INTO schema_migrations (migration) VALUES (?)",
            (migration_name,)
        )
        
        conn.commit()
        logger.info("Migration completed: %s", migration_name)
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error("Migration failed: %s - %s", migration_name, e)
        return False


def run_migrations() -> dict:
    """
    Run all pending migrations.
    
    Returns:
        Dict with 'success' (bool), 'applied' (int), 'failed' (int), 'errors' (list)
    """
    db_path = Path(DATABASE_PATH)
    if not db_path.exists():
        logger.warning("Database does not exist, cannot run migrations: %s", db_path)
        return {"success": False, "applied": 0, "failed": 0, "errors": ["Database does not exist"]}
    
    conn = sqlite3.connect(db_path)
    try:
        # Ensure migrations table exists
        ensure_migrations_table(conn)
        
        # Get applied migrations
        applied = get_applied_migrations(conn)
        
        # Get pending migrations
        pending = get_pending_migrations()
        
        # Filter out already applied migrations
        to_run = [m for m in pending if m.name not in applied]
        
        if not to_run:
            logger.info("No pending migrations to run")
            return {"success": True, "applied": 0, "failed": 0, "errors": []}
        
        logger.info("Found %d pending migrations", len(to_run))
        
        # Run migrations
        results = {"success": True, "applied": 0, "failed": 0, "errors": []}
        
        for migration_path in to_run:
            if run_migration(conn, migration_path):
                results["applied"] += 1
            else:
                results["failed"] += 1
                results["success"] = False
                results["errors"].append(migration_path.name)
        
        return results
        
    finally:
        conn.close()


def get_migration_status() -> dict:
    """Get current migration status."""
    db_path = Path(DATABASE_PATH)
    if not db_path.exists():
        return {"exists": False, "applied": [], "pending": []}
    
    conn = sqlite3.connect(db_path)
    try:
        ensure_migrations_table(conn)
        applied = get_applied_migrations(conn)
        pending = [m.name for m in get_pending_migrations() if m.name not in applied]
        
        return {
            "exists": True,
            "applied": sorted(applied),
            "pending": pending,
        }
    finally:
        conn.close()
